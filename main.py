from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from mutagen.mp3 import MP3
from mutagen.wave import WAVE

from datetime import datetime

from controller.config import Config
from controller.database import db
from controller.models import (
    User, Role, Genre, Song, Artist,
    Playlist, PlaylistSong, Notification
)
from sqlalchemy.orm import joinedload

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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password_hash, request.form["password"]):
            session["user_id"] = user.user_id
            session["username"] = user.username
            roles = [r.role_name for r in user.roles]
            session["roles"] = roles

            if 'ADMIN' in roles:
                return redirect(url_for("admin_dashboard"))
            elif 'CREATOR' in roles:
                return redirect(url_for("creator_dashboard"))
            elif 'USER' in roles:
                return redirect(url_for("user_dashboard"))
            else:
                flash("No valid role assigned", "error")
                return redirect(url_for("login"))

        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))

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

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ================= ADMIN =================
@app.route("/dashboard/admin")
def admin_dashboard():
    if 'ADMIN' not in session.get('roles', []):
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    all_users = User.query.all()

    normal_user_list = [
        u for u in all_users
        if 'USER' in [r.role_name for r in u.roles] and 'CREATOR' not in [r.role_name for r in u.roles]
    ]

    creator_list = [
        u for u in all_users
        if 'CREATOR' in [r.role_name for r in u.roles]
    ]

    normal_users = len(normal_user_list)
    creators = len(creator_list)
    total_songs = Song.query.count()

    songs_by_genre = {}
    for song in Song.query.options(joinedload(Song.creator)).all():
        g = song.genre.genre_name
        songs_by_genre.setdefault(g, []).append(song)

    return render_template(
        "admin_dashboard.html",
        user=user,
        normal_users=normal_users,
        creators=creators,
        total_songs=total_songs,
        songs_by_genre=songs_by_genre,
        normal_user_list=normal_user_list,
        creator_list=creator_list
    )


@app.route("/admin/block/user/<int:user_id>", methods=["POST"])
def admin_block_user(user_id):
    if 'ADMIN' not in session.get('roles', []):
        return "Unauthorized", 403

    user = User.query.get_or_404(user_id)
    user.is_blocked = True
    db.session.commit()

    notif = Notification(
        user_id=user_id,
        message="Your account has been blocked by admin."
    )
    db.session.add(notif)
    db.session.commit()

    return '', 204


@app.route("/admin/unblock/user/<int:user_id>", methods=["POST"])
def admin_unblock_user(user_id):
    if 'ADMIN' not in session.get('roles', []):
        return "Unauthorized", 403

    user = User.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()

    notif = Notification(
        user_id=user_id,
        message="Your account has been unblocked."
    )
    db.session.add(notif)
    db.session.commit()

    return '', 204


@app.route("/admin/delete/song/<int:song_id>", methods=["POST"])
def admin_delete_song(song_id):
    if 'ADMIN' not in session.get('roles', []):
        return "Unauthorized", 403

    reason = request.form.get("reason", "No reason provided").strip()
    if not reason:
        reason = "No reason provided"

    song = Song.query.get_or_404(song_id)
    creator_id = song.creator_id

    notif = Notification(
        user_id=creator_id,
        message=f"Your song '{song.title}' was deleted by admin. Reason: {reason}"
    )
    db.session.add(notif)

    PlaylistSong.query.filter_by(song_id=song_id).delete()
    db.session.delete(song)
    db.session.commit()

    flash("Song deleted successfully and creator notified.", "success")
    return redirect(url_for("admin_dashboard"))


# ================= CREATOR =================
@app.route("/dashboard/creator")
def creator_dashboard(blocked_upload=None):
    if 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    is_blocked = user.is_blocked if user else False

    songs = Song.query.options(joinedload(Song.genre)).filter_by(creator_id=session["user_id"]).all()
    total_songs = len(songs)
    top_song = max(songs, key=lambda s: s.play_count, default=None) if songs else None

    notifications = Notification.query.filter_by(user_id=session["user_id"]).order_by(Notification.timestamp.desc()).all()

    return render_template(
        "creator_dashboard.html",
        username=session["username"],
        genres=Genre.query.all(),
        songs=songs,
        total_songs=total_songs,
        top_song=top_song,
        notifications=notifications,
        blocked_upload=blocked_upload,
        is_blocked=is_blocked
    )


@app.route("/creator/upload", methods=["POST"])
def creator_upload():
    if 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if user.is_blocked:
        return redirect(url_for("creator_dashboard", blocked_upload=1))

    file = request.files["song"]
    title = request.form["title"]
    genre_id = int(request.form["genre_id"])

    if not allowed_file(file.filename):
        flash("Invalid file type", "error")
        return redirect(url_for("creator_dashboard"))

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

    flash("Song uploaded successfully!", "success")
    return redirect(url_for("creator_dashboard"))


@app.route("/creator/edit/<int:song_id>", methods=["POST"])
def edit_song(song_id):
    if 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    song = Song.query.get_or_404(song_id)
    if song.creator_id != session["user_id"]:
        return "Unauthorized", 403

    song.title = request.form["title"]
    db.session.commit()

    return redirect(url_for("creator_dashboard"))


@app.route("/creator/delete/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    if 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    song = Song.query.get_or_404(song_id)
    if song.creator_id != session["user_id"]:
        return "Unauthorized", 403

    PlaylistSong.query.filter_by(song_id=song_id).delete()
    db.session.delete(song)
    db.session.commit()

    return redirect(url_for("creator_dashboard"))


@app.route("/dashboard/analytics")
def creator_analytics():
    if 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    songs = Song.query.filter_by(creator_id=session["user_id"]).all()
    total_songs = len(songs)
    top_song = max(songs, key=lambda s: s.play_count, default=None) if songs else None
    notifications = Notification.query.filter_by(user_id=session["user_id"]).order_by(Notification.timestamp.desc()).all()

    return render_template("creator_analytics.html",
                           username=session["username"],
                           total_songs=total_songs,
                           top_song=top_song,
                           notifications=notifications)


# ================= USER DASHBOARD (FOR BOTH REGULAR USERS AND CREATORS IN USER MODE) =================
@app.route("/dashboard/user")
def user_dashboard():
    # Allow both USER and CREATOR roles
    roles = session.get('roles', [])
    if 'USER' not in roles and 'CREATOR' not in roles:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    current_user = User.query.get(user_id)

    if not current_user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    songs = Song.query.options(
        joinedload(Song.genre),
        joinedload(Song.artists)
    ).all()

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()

    return render_template(
        "user_dashboard.html",
        username=session["username"],
        songs=songs,
        playlists=Playlist.query.filter_by(user_id=user_id).all(),
        active_playlist=None,
        notifications=notifications,
        is_blocked=current_user.is_blocked
    )


@app.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    user_id = session.get("user_id")
    if playlist.user_id != user_id:
        return "Unauthorized", 403

    current_user = User.query.get(user_id)
    if not current_user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    songs = (
        Song.query.options(
            joinedload(Song.genre),
            joinedload(Song.artists)
        )
        .join(PlaylistSong)
        .filter(PlaylistSong.playlist_id == playlist_id)
        .order_by(PlaylistSong.position)
        .all()
    )

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()

    return render_template(
        "user_dashboard.html",
        username=session["username"],
        songs=songs,
        playlists=Playlist.query.filter_by(user_id=user_id).all(),
        active_playlist=playlist,
        notifications=notifications,
        is_blocked=current_user.is_blocked
    )


# ================= PLAYLIST ROUTES =================
@app.route("/playlist/create", methods=["POST"])
def create_playlist():
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
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
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    playlist_id = int(request.form["playlist_id"])
    song_id = int(request.form["song_id"])

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    if PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first():
        return redirect(request.referrer or url_for("user_dashboard"))

    next_position = (db.session.query(db.func.max(PlaylistSong.position))
                    .filter_by(playlist_id=playlist_id).scalar() or 0) + 1

    db.session.add(PlaylistSong(playlist_id=playlist_id, song_id=song_id, position=next_position))
    db.session.commit()

    return redirect(request.referrer or url_for("user_dashboard"))


@app.route("/playlist/rename/<int:playlist_id>", methods=["POST"])
def rename_playlist(playlist_id):
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != session["user_id"]:
        return "Unauthorized", 403

    playlist.playlist_name = request.form["name"].strip()
    db.session.commit()
    return redirect(url_for("user_dashboard"))


@app.route("/playlist/delete/<int:playlist_id>", methods=["POST"])
def delete_playlist(playlist_id):
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
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
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
        return redirect(url_for("login"))

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
    if 'USER' not in session.get('roles', []) and 'CREATOR' not in session.get('roles', []):
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


# ================= PROFILE ROUTES =================
@app.route("/profile")
def profile():
    roles = session.get('roles', [])
    if 'ADMIN' not in roles and 'USER' not in roles and 'CREATOR' not in roles:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    roles = session.get('roles', [])
    if 'ADMIN' not in roles and 'USER' not in roles and 'CREATOR' not in roles:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        username = request.form["username"].strip()
        if username and username != user.username:
            if User.query.filter_by(username=username).first():
                flash("Username already taken", "error")
            else:
                user.username = username
                session["username"] = username
                db.session.commit()
                flash("Profile updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=user)


@app.route("/profile/change-password", methods=["GET", "POST"])
def change_password():
    roles = session.get('roles', [])
    if 'ADMIN' not in roles and 'USER' not in roles and 'CREATOR' not in roles:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        current = request.form["current_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if not check_password_hash(user.password_hash, current):
            flash("Current password is incorrect", "error")
        elif new != confirm:
            flash("New passwords do not match", "error")
        elif len(new) < 6:
            flash("New password must be at least 6 characters", "error")
        else:
            user.password_hash = generate_password_hash(new)
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for("profile"))

    return render_template("change_password.html", user=user)


# ================= PLAY COUNT API =================
@app.route('/api/song/<int:song_id>/play', methods=['POST'])
def increment_play(song_id):
    song = Song.query.get_or_404(song_id)

    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.is_blocked:
            return '', 403

        if 'USER' in session.get('roles', []) or 'CREATOR' in session.get('roles', []):
            song.play_count += 1
            db.session.commit()

    return '', 204


# ================= RUN =================
if __name__ == "__main__":
    app.run()