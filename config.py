import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    # Database Configuration
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME')
    DB_PORT = "5432"

    # PostgreSQL Connection String
    if DB_USER and DB_PASSWORD and DB_HOST and DB_NAME:
        SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URI", "sqlite:///chemicals.db")  # Fallback to SQLite
