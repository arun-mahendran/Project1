from controller.database import db


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    roles = db.relationship(
        'Role',
        secondary='user_roles',
        backref=db.backref('users', lazy=True)
    )


class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)


class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)


class Genre(db.Model):
    __tablename__ = 'genres'
    genre_id = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String(50), unique=True, nullable=False)


class Artist(db.Model):
    __tablename__ = 'artists'
    artist_id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(100), unique=True, nullable=False)
    artist_bio = db.Column(db.Text)


class Song(db.Model):
    __tablename__ = 'songs'

    song_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    # REQUIRED FOR UPLOAD
    file_path = db.Column(db.String(255), nullable=False)

    # TEMP: allow NULL until duration logic added
    duration = db.Column(db.Integer, nullable=True)

    # NEW: Track how many times the song was played
    play_count = db.Column(db.Integer, default=0)

    # WHO UPLOADED THE SONG
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    genre_id = db.Column(db.Integer, db.ForeignKey('genres.genre_id'), nullable=False)

    genre = db.relationship('Genre', backref=db.backref('songs', lazy=True))
    creator = db.relationship('User', backref=db.backref('uploaded_songs', lazy=True))



class SongArtist(db.Model):
    __tablename__ = 'song_artists'
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.artist_id'), nullable=False)

    song = db.relationship('Song', backref=db.backref('song_artists', lazy=True))
    artist = db.relationship('Artist', backref=db.backref('song_artists', lazy=True))


class Playlist(db.Model):
    __tablename__ = 'playlists'
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    user = db.relationship('User', backref=db.backref('playlists', lazy=True))


class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.playlist_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    playlist = db.relationship('Playlist', backref=db.backref('playlist_songs', lazy=True))
    song = db.relationship('Song', backref=db.backref('playlist_songs', lazy=True))

