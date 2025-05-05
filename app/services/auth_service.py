# app/services/auth_service.py
import jwt
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash
from app.models.user_model import User
from flask import current_app

SECRET_KEY = 'sua_chave_secreta'

def generate_token(username):
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    token = jwt.encode({'username': username, 'exp': expiration}, SECRET_KEY, algorithm="HS256")
    return token

def authenticate_user(username, password):
    user = User.get_user(username)
    if user and check_password_hash(user['password'], password):
        return generate_token(username)
    return None

def verify_token(token):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = User.get_user(data['username'])
        return user if user else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
