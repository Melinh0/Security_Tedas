from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def role_required(required_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Permitir admin acessar tudo
            if user_role == 'admin':
                return fn(*args, **kwargs)
            
            # Se for uma string única, converter para lista
            if isinstance(required_roles, str):
                required_roles_list = [required_roles]
            else:
                required_roles_list = required_roles
                
            # Verificar se a role do usuário está nas permitidas
            if user_role not in required_roles_list:
                return jsonify({"message": "Acesso negado"}), 403
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator