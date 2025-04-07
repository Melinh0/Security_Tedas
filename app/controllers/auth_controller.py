# app/controllers/auth_controller.py
from flask import Blueprint, request, jsonify
from app.services.user_service import create_user, update_password, delete_user
from app.middleware.auth_middleware import token_required, requires_role

user_bp = Blueprint('user', __name__)

@user_bp.route('/create_user', methods=['POST'])
@token_required
@requires_role(['admin'])
def create_new_user(username, current_user):
    data = request.json
    new_username = data.get('username')
    new_password = data.get('password')
    new_roles = data.get('roles', ['user'])

    if create_user(new_username, new_password, new_roles):
        return jsonify({'message': 'Usuário criado com sucesso!'}), 201
    return jsonify({'message': 'Usuário já existe!'}), 400

@user_bp.route('/update_password', methods=['PUT'])
@token_required
def update_user_password(username, current_user):
    data = request.json
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({'message': 'Nova senha não fornecida!'}), 400

    if update_password(username, new_password):
        return jsonify({'message': 'Senha atualizada com sucesso!'}), 200
    return jsonify({'message': 'Erro ao atualizar senha!'}), 400

@user_bp.route('/delete_user/<string:target_username>', methods=['DELETE'])
@token_required
@requires_role(['admin'])
def remove_user(username, current_user, target_username):
    if delete_user(target_username):
        return jsonify({'message': 'Usuário deletado com sucesso!'}), 200
    return jsonify({'message': 'Usuário não encontrado!'}), 404
