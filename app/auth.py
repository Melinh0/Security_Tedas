#auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from flasgger.utils import swag_from

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from .models import User
from .__init__ import db  # db é importado de __init__.py

@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True,
         'schema': {'type': 'object', 'properties': {
             'username': {'type': 'string'},
             'password': {'type': 'string'},
             'role': {'type': 'string'}
         }}}],
    'responses': {200: {'description': 'User created successfully'}}
})
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400

    new_user = User(username=data['username'], role=data['role'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 200

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True,
         'schema': {'type': 'object', 'properties': {
             'username': {'type': 'string'},
             'password': {'type': 'string'}
         }}}],
    'responses': {200: {'description': 'Token JWT'}}})
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"msg": "Bad username or password"}), 401

    # Geração do token com o identity como dicionário
    token = create_access_token(
        identity={'username': user.username, 'role': user.role},  # identity como dicionário
        additional_claims={'sub': user.username}
    )
    return jsonify(access_token=token)


# Aqui está o trecho de código que seria usado para obter o usuário autenticado
@auth_bp.route('/protected', methods=['GET'])
def protected():
    identity = get_jwt_identity()  # Isso retorna o dicionário com 'username' e 'role'

    # Verificando se identity é um dicionário, para garantir que não seja uma string
    if isinstance(identity, dict):
        if identity['role'] not in ['admin', 'user']:  # Exemplo de verificação de role
            return jsonify({"msg": "You do not have the required permissions"}), 403
    else:
        return jsonify({"msg": "Invalid identity format"}), 400

    return jsonify({"msg": "You have access to this protected resource!"}), 200
