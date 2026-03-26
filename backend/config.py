import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "./.flask_sessions"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    DEFAULT_IMAP_HOST = os.getenv("IMAP_HOST", "")
    DEFAULT_SMTP_HOST = os.getenv("SMTP_HOST", "")
    DEFAULT_SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    DEFAULT_IMAP_PORT = int(os.getenv("IMAP_PORT", 993))