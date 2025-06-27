# app/controllers/admin_controller.py
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.admin import Admin
from app.models.log import Log
from app import db
from app.utils.decorators import role_required

def registrar_log(usuario_id, acao):
    novo_log = Log(usuario_id=usuario_id, acao=acao)
    db.session.add(novo_log)
    db.session.commit()

@jwt_required()
@role_required('admin')
def get_admins():
    current_admin_id = int(get_jwt_identity())
    admins = Admin.query.all()
    
    registrar_log(current_admin_id, 'LISTAR_ADMINS')
    return jsonify([admin.to_dict() for admin in admins]), 200

@jwt_required()
@role_required('admin')
def create_admin():
    current_admin_id = int(get_jwt_identity())
    data = request.get_json()
    
    required_fields = ['username', 'password', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Email, usuário e senha são obrigatórios"}), 400
    
    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username já está em uso"}), 400
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email já está em uso"}), 400
    
    new_admin = Admin(
        username=data['username'],
        email=data['email'],
        role='admin'
    )
    new_admin.set_password(data['password'])
    db.session.add(new_admin)
    db.session.commit()
    
    registrar_log(current_admin_id, f'CRIAR_ADMIN:{new_admin.id}')
    return jsonify(new_admin.to_dict()), 201

@jwt_required()
@role_required('admin')
def update_admin():
    current_admin_id = int(get_jwt_identity())
    admin = Admin.query.get(current_admin_id)
    data = request.get_json()
    
    if 'email' in data:
        if Admin.query.filter(Admin.email == data['email'], Admin.id != current_admin_id).first():
            return jsonify({"message": "Email já está em uso"}), 400
        admin.email = data['email']
    
    if 'username' in data:
        admin.username = data['username']
    
    if 'password' in data:
        admin.set_password(data['password'])
    
    db.session.commit()
    
    registrar_log(current_admin_id, 'ATUALIZAR_ADMIN')
    return jsonify(admin.to_dict()), 200

@jwt_required()
@role_required('admin')
def get_users():
    current_admin_id = int(get_jwt_identity())
    users = Admin.query.filter_by(role='user').all()
    
    registrar_log(current_admin_id, 'LISTAR_USERS')
    return jsonify([user.to_dict() for user in users]), 200

@jwt_required()
@role_required('admin')
def create_user():
    current_admin_id = int(get_jwt_identity())
    data = request.get_json()
    
    required_fields = ['username', 'password', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Email, usuário e senha são obrigatórios"}), 400
    
    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username já está em uso"}), 400
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email já está em uso"}), 400
    
    new_user = Admin(
        username=data['username'],
        email=data['email'],
        role='user'
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    registrar_log(current_admin_id, f'CRIAR_USER:{new_user.id}')
    return jsonify(new_user.to_dict()), 201

@jwt_required()
@role_required('admin')
def delete_admin(admin_id):
    current_admin_id = int(get_jwt_identity())
    
    if current_admin_id == admin_id:
        return jsonify({"message": "Você não pode deletar a si mesmo"}), 400
    
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"message": "Admin não encontrado"}), 404
    
    if admin.username == 'admin':
        return jsonify({"message": "Não é permitido deletar o admin padrão"}), 400
    
    db.session.delete(admin)
    db.session.commit()
    
    registrar_log(current_admin_id, f'DELETE_ADMIN:{admin_id}')
    return jsonify({"message": "Admin deletado com sucesso"}), 200

@jwt_required()
@role_required('admin')
def delete_user(user_id):
    current_admin_id = int(get_jwt_identity())
    
    user = Admin.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    
    if user.username == 'user':
        return jsonify({"message": "Não é permitido deletar o usuário padrão"}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    registrar_log(current_admin_id, f'DELETE_USER:{user_id}')
    return jsonify({"message": "Usuário deletado com sucesso"}), 200

@jwt_required()
@role_required('admin')
def get_logs():
    logs = Log.query.order_by(Log.data_hora.desc()).all()
    return jsonify([log.to_dict() for log in logs]), 200