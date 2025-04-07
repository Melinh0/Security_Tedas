# app/controllers/user_controller.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user_model import User, db

# Criação do Blueprint
user_bp = Blueprint('user_bp', __name__)

# Rota para criar um novo usuário
@user_bp.route('/users', methods=['POST'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Cria um novo usuário',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'novo_usuario'},
                    'password': {'type': 'string', 'example': 'senha123'},
                    'roles': {'type': 'array', 'items': {'type': 'string'}, 'example': ['user']}
                }
            }
        }
    ],
    'responses': {
        '201': {'description': 'Usuário criado com sucesso'},
        '400': {'description': 'Erro na requisição'}
    }
})
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Dados inválidos'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password_hash=hashed_password, roles=','.join(data.get('roles', ['user'])))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuário criado com sucesso!'}), 201

# Rota para obter todos os usuários
@user_bp.route('/users', methods=['GET'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Obtém a lista de usuários',
    'responses': {
        '200': {
            'description': 'Lista de usuários',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'username': {'type': 'string'},
                        'roles': {'type': 'array', 'items': {'type': 'string'}}
                    }
                }
            }
        }
    }
})

def get_users():
    try:
        # Certifique-se de que o app está no contexto antes de fazer a consulta
        with db.session.begin():
            users = User.query.all()
            return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Rota para obter um usuário pelo nome
@user_bp.route('/users/<string:username>', methods=['GET'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Obtém um usuário pelo nome',
    'parameters': [
        {
            'name': 'username',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nome do usuário'
        }
    ],
    'responses': {
        '200': {'description': 'Usuário encontrado'},
        '404': {'description': 'Usuário não encontrado'}
    }
})
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'username': user.username, 'roles': user.roles.split(',')}), 200
    return jsonify({'message': 'Usuário não encontrado'}), 404

# Rota para deletar um usuário
@user_bp.route('/users/<string:username>', methods=['DELETE'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Deleta um usuário',
    'parameters': [
        {
            'name': 'username',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nome do usuário'
        }
    ],
    'responses': {
        '200': {'description': 'Usuário deletado'},
        '404': {'description': 'Usuário não encontrado'}
    }
})
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuário deletado com sucesso!'}), 200
