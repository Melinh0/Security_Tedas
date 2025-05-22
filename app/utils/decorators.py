#app/utils/decorators.py
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['role'] != required_role:
                return jsonify({"message": "Acesso negado"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator