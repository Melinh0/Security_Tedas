# app/middleware/auth_middleware.py
from flask import request, jsonify
from functools import wraps
import jwt
from app.models.user_model import User
import logging

SECRET_KEY = 'sua_chave_secreta'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            logging.warning("Token ausente")
            return jsonify({'message': 'Token ausente!'}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.get_user(data['username'])
            if not current_user:
                logging.warning("Usuário não encontrado")
                return jsonify({'message': 'Usuário não encontrado!'}), 401
        except jwt.ExpiredSignatureError:
            logging.warning("Token expirado")
            return jsonify({'message': 'Token expirado!'}), 401
        except jwt.InvalidTokenError:
            logging.warning("Token inválido")
            return jsonify({'message': 'Token inválido!'}), 401
        return f(data['username'], current_user, *args, **kwargs)
    return decorated

def requires_role(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(username, current_user, *args, **kwargs):
            user_roles = current_user.get('roles', [])
            if any(role in required_roles for role in user_roles):
                return f(username, current_user, *args, **kwargs)
            else:
                logging.warning("Permissão negada")
                return jsonify({'message': 'Permissão negada!'}), 403
        return decorated_function
    return decorator
