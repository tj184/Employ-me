import os
from dotenv import load_dotenv



basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


class Config:
    # Flask secret key
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    # PostgreSQL database hosted on Render
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing. "
            "Please configure PostgreSQL in Render environment variables."
        )

    # Normalize older PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    # Upload configuration
    UPLOAD_FOLDER = os.path.join(
        basedir,
        "static/uploads"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif"
    }

    # Google reCAPTCHA
    RECAPTCHA_SITE_KEY = os.environ.get(
        "RECAPTCHA_SITE_KEY"
    )

    RECAPTCHA_SECRET_KEY = os.environ.get(
        "RECAPTCHA_SECRET_KEY"
    )
