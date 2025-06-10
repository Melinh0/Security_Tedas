#app/config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-supersecretkey")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "wecemailtest@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "rawr sfne fxqy awwh")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # limite de 16MB por arquivo (ajuste à vontade)
    ALLOWED_EXTENSIONS = None  # None = aceita qualquer extensão; você pode listar ['jpg','png','pdf',...] se quiser restringir