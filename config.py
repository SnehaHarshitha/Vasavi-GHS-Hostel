import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pg-hostel-mess-fallback-key-2026'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/pg_hostel_mess'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'pg_hostel_mess'
    
    # Mail settings (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # Maps
    GOOGLE_MAPS_EMBED_URL = os.environ.get(
        'GOOGLE_MAPS_EMBED_URL',
        'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3824.238600865866!2d81.47450377484433!3d16.814467383979857!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a37e584f23e6fb3%3A0xe54e386eb027003f!2sSri%20Vasavi%20Engineering%20College!5e0!3m2!1sen!2sin!4v1711000000000!5m2!1sen!2sin'
    )

    # Maximum file upload size: 5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'dev': DevelopmentConfig,
    'development': DevelopmentConfig,
    'prod': ProductionConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
