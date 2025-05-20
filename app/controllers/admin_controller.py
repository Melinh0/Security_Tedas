#admin.controller.py
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from app.models.admin import Admin
from app import db
from app.utils.decorators import role_required
from app import jwt  

def login():
    data = request.get_json()
    admin = Admin.query.filter_by(username=data.get('username')).first()
    
    if not admin or not admin.check_password(data.get('password')):
        return jsonify({"message": "Credenciais inválidas"}), 401
    
    # Corrigido: identity deve ser string
    access_token = create_access_token(
        identity=str(admin.id),  # Convertido para string
        additional_claims={"role": admin.role}
    )
    return jsonify(access_token=access_token), 200

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Admin.query.get(int(identity))  # Convertendo de volta para int

@jwt_required()
@role_required('admin')
def get_admins():
    admins = Admin.query.all()
    return jsonify([admin.to_dict() for admin in admins]), 200

@jwt_required()
@role_required('admin')
def create_admin():
    data = request.get_json()
    
    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Nome de usuário já existe"}), 400
    
    new_admin = Admin(username=data['username'])
    new_admin.set_password(data['password'])
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify(new_admin.to_dict()), 201

@jwt_required()
@role_required('admin')
def update_admin():
    # Corrigido: converter identity para int
    current_admin_id = int(get_jwt_identity())
    admin = Admin.query.get(current_admin_id)
    data = request.get_json()
    
    if 'username' in data:
        admin.username = data['username']
    if 'password' in data:
        admin.set_password(data['password'])
    
    db.session.commit()
    return jsonify(admin.to_dict()), 200