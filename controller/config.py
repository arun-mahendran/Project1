import os


class Config:
    # ================= Security =================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # ================= Database =================
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Fix for Render / Heroku style postgres URLs
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///msa.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= Optional (for migration scripts only) =================
SQLITE_DB_URI = "sqlite:///msa.sqlite3"

POSTGRES_DB_URI = os.getenv("DATABASE_URL")
if POSTGRES_DB_URI and POSTGRES_DB_URI.startswith("postgres://"):
    POSTGRES_DB_URI = POSTGRES_DB_URI.replace("postgres://", "postgresql://", 1)
