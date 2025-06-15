#views.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User
from flasgger.utils import swag_from
from functools import wraps  

view_bp = Blueprint('view', __name__, url_prefix='/api')

def role_required(roles):
    def wrapper(func):
        @jwt_required()
        @wraps(func)
        def inner(*args, **kwargs):
            identity = get_jwt_identity()
            print("JWT identity:", identity)  # Log the identity
            if 'role' not in identity or identity['role'] not in roles:
                return jsonify({'msg': 'Access denied'}), 403
            return func(*args, **kwargs)
        return inner
    return wrapper

@view_bp.route('/users', methods=['GET'])
@swag_from({
    'tags': ['Users'],
    'responses': {200: {'description': 'Users visible to public'}},
    'security': [{'jwt_token': []}]
})
@role_required(['admin'])
def get_all_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in users])

@view_bp.route('/public', methods=['GET'])
@swag_from({
    'tags': ['Public'],
    'responses': {200: {'description': 'Users visible to public'}},
    'security': [{'jwt_token': []}]
})
@jwt_required()  # Permite que qualquer usuário autenticado acesse
def get_all_public():
    public_users = User.query.filter_by(role='public').all()
    return jsonify([{'id': u.id, 'username': u.username} for u in public_users])

@view_bp.route('/visible-users', methods=['GET'])
@swag_from({
    'tags': ['Public'],
    'responses': {200: {'description': 'Users visible to public'}},
    'security': [{'jwt_token': []}]
})
@role_required(['admin', 'user'])  # Permitido para 'admin' e 'user'
def public_view():
    users = User.query.filter(User.role != 'admin').all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in users])
