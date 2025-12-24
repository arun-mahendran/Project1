from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from mutagen.mp3 import MP3
from mutagen.wave import WAVE

from controller.config import Config
from controller.database import db
from controller.models import (
    User, Role, Genre, Song,
    Playlist, PlaylistSong
)
from sqlalchemy.orm import joinedload  # NEW IMPORT to fix potential lazy load errors

# ================= APP SETUP =================
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"mp3", "wav"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= DB INIT =================
with app.app_context():
    db.create_all()

    for r in ["ADMIN", "CREATOR", "USER"]:
        if not Role.query.filter_by(role_name=r).first():
            db.session.add(Role(role_name=r))

    if not Genre.query.first():
        db.session.add_all([
            Genre(genre_name="Pop"),
            Genre(genre_name="Rock"),
            Genre(genre_name="Hip-Hop"),
            Genre(genre_name="Classical")
        ])

    db.session.commit()

    admin = User.query.filter_by(email="admin@tunex.com").first()
    if not admin:
        admin = User(
            username="TUNEX_ADMIN",
            email="admin@tunex.com",
            password_hash=generate_password_hash("admin123")
        )
        admin.roles.append(Role.query.filter_by(role_name="ADMIN").first())
        db.session.add(admin)
        db.session.commit()


# ================= AUTH =================
@app.route("/")
def index():
    return render_template("index.html")


from flask import flash  # ← Add this import at the top

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        role = request.form["role"]

        if user and check_password_hash(user.password_hash, request.form["password"]):
            if role not in [r.role_name for r in user.roles]:
                flash("Unauthorized role selected", "error")
                return redirect(url_for("login") + f"?role={role}")

            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = role

            if role == "CREATOR":
                return redirect(url_for("creator_dashboard"))
            if role == "USER":
                return redirect(url_for("user_dashboard"))

        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("login") + f"?role={role}")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        role_name = request.form.get("role")

        if not all([email, username, password, role_name]):
            return "Missing fields", 400

        if User.query.filter_by(email=email).first():
            return "Email already exists"

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            return "Invalid role"

        user.roles.append(role)
        db.session.add(user)
        db.session.commit()

        # SUCCESS: Redirect to login with the role pre-selected
        return redirect(url_for("login") + f"?role={role_name}")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ================= CREATOR =================
@app.route("/dashboard/creator")
def creator_dashboard():
    if session.get("role") != "CREATOR":
        return redirect(url_for("login"))

    songs = Song.query.options(joinedload(Song.genre)).filter_by(creator_id=session["user_id"]).all()

    # Calculate analytics
    total_songs = len(songs)
    total_plays = sum(song.play_count for song in songs)
    top_song = max(songs, key=lambda s: s.play_count, default=None) if songs else None

    return render_template(
        "creator_dashboard.html",
        username=session["username"],
        genres=Genre.query.all(),
        songs=songs,
        total_songs=total_songs,
        total_plays=total_plays,
        top_song=top_song
    )

# ================= PLAY COUNT API =================
@app.route('/api/song/<int:song_id>/play', methods=['POST'])
def increment_play(song_id):
    song = Song.query.get_or_404(song_id)

    # Only count if logged-in and is a regular USER
    if 'user_id' in session and session.get('role') == 'USER':
        song.play_count += 1
        db.session.commit()

    return '', 204


@app.route("/creator/upload", methods=["POST"])
def creator_upload():
    if session.get("role") != "CREATOR":
        return redirect(url_for("login"))

    file = request.files["song"]
    title = request.form["title"]
    genre_id = int(request.form["genre_id"])

    if not allowed_file(file.filename):
        return "Invalid file"

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    duration = (
        int(MP3(path).info.length)
        if filename.endswith(".mp3")
        else int(WAVE(path).info.length)
    )

    song = Song(
        title=title,
        file_path=path,
        duration=duration,
        creator_id=session["user_id"],
        genre_id=genre_id
    )

    db.session.add(song)
    db.session.commit()

    return redirect(url_for("creator_dashboard"))


@app.route("/creator/edit/<int:song_id>", methods=["POST"])
def edit_song(song_id):
    if session.get("role") != "CREATOR":
        return redirect(url_for("login"))

    song = Song.query.get_or_404(song_id)

    if song.creator_id != session["user_id"]:
        return "Unauthorized", 403

    song.title = request.form["title"]
    db.session.commit()

    return redirect(url_for("creator_dashboard"))


@app.route("/creator/delete/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    if session.get("role") != "CREATOR":
        return redirect(url_for("login"))

    song = Song.query.get_or_404(song_id)

    if song.creator_id != session["user_id"]:
        return "Unauthorized", 403

    PlaylistSong.query.filter_by(song_id=song_id).delete()
    db.session.delete(song)
    db.session.commit()

    return redirect(url_for("creator_dashboard"))


# ================= USER =================
@app.route("/dashboard/user")
def user_dashboard():
    if session.get("role") != "USER":
        return redirect(url_for("login"))

    songs = Song.query.options(joinedload(Song.genre)).all()  # NEW: eager load genre

    return render_template(
        "user_dashboard.html",
        username=session["username"],
        songs=songs,
        playlists=Playlist.query.filter_by(user_id=session["user_id"]).all(),
        active_playlist=None
    )


# ================= PLAYLIST =================
@app.route("/playlist/create", methods=["POST"])
def create_playlist():
    if session.get("role") != "USER":
        return redirect(url_for("login"))

    playlist = Playlist(
        playlist_name=request.form["name"],
        user_id=session["user_id"]
    )

    db.session.add(playlist)
    db.session.commit()

    return redirect(url_for("user_dashboard"))


@app.route("/playlist/add", methods=["POST"])
def add_song_to_playlist():
    if session.get("role") != "USER":
        return redirect(url_for("login"))

    playlist_id = request.form.get("playlist_id")
    song_id = request.form.get("song_id")

    if not playlist_id or not song_id:
        return redirect(request.referrer or url_for("user_dashboard"))

    playlist_id = int(playlist_id)
    song_id = int(song_id)

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    # prevent duplicates
    exists = PlaylistSong.query.filter_by(
        playlist_id=playlist_id,
        song_id=song_id
    ).first()

    if exists:
        return redirect(request.referrer or url_for("user_dashboard"))

    # calculate next position
    last_position = (
        db.session.query(db.func.max(PlaylistSong.position))
        .filter_by(playlist_id=playlist_id)
        .scalar()
    )

    next_position = (last_position or 0) + 1

    db.session.add(
        PlaylistSong(
            playlist_id=playlist_id,
            song_id=song_id,
            position=next_position
        )
    )
    db.session.commit()

    return redirect(request.referrer or url_for("user_dashboard"))



@app.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    songs = (
        Song.query.options(joinedload(Song.genre))  # NEW: eager load
        .join(PlaylistSong)
        .filter(PlaylistSong.playlist_id == playlist_id)
        .all()
    )

    return render_template(
        "user_dashboard.html",
        username=session["username"],
        songs=songs,
        playlists=Playlist.query.filter_by(user_id=session["user_id"]).all(),
        active_playlist=playlist
    )


@app.route("/playlist/rename/<int:playlist_id>", methods=["POST"])
def rename_playlist(playlist_id):
    if session.get("role") != "USER":
        return redirect(url_for("login"))

    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    playlist.playlist_name = request.form["name"].strip()
    db.session.commit()

    return redirect(url_for("user_dashboard"))


@app.route("/playlist/delete/<int:playlist_id>", methods=["POST"])
def delete_playlist(playlist_id):
    if session.get("role") != "USER":
        return redirect(url_for("login"))

    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
    db.session.delete(playlist)
    db.session.commit()

    return redirect(url_for("user_dashboard"))

@app.route('/playlist/remove', methods=['POST'])
def remove_from_playlist():
    if session.get('role') != 'USER':
        return redirect(url_for('login'))

    playlist_id = int(request.form['playlist_id'])
    song_id = int(request.form['song_id'])

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != session['user_id']:
        return "Unauthorized", 403

    PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).delete()
    db.session.commit()

    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/playlist/reorder/<int:playlist_id>', methods=['POST'])
def reorder_playlist(playlist_id):
    if session.get('role') != 'USER':
        return '', 403

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != session['user_id']:
        return '', 403

    data = request.get_json()
    order = data['order']

    for item in order:
        ps = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=item['song_id']).first()
        if ps:
            ps.position = item['position']

    db.session.commit()
    return '', 204


# ================= RUN =================
if __name__ == "__main__":
    app.run()