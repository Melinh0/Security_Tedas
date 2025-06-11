#app/controllers/admin.controller.py
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
)
from flask_mail import Message
from app.models.admin import Admin
from app.models.log import Log
from app import db
from app.utils.decorators import role_required
from app import jwt  
from app import mail
from datetime import datetime, timedelta
import secrets
import os
from werkzeug.utils import secure_filename

def registrar_log(usuario_id, acao):
    """Registra uma ação no log"""
    novo_log = Log(usuario_id=usuario_id, acao=acao)
    db.session.add(novo_log)
    db.session.commit()

def login():
    data = request.get_json()
    admin = Admin.query.filter(
        (Admin.email == data.get('username')) | 
        (Admin.username == data.get('username'))
    ).first()
    
    if not admin or not admin.check_password(data.get('password')):
        return jsonify({"message": "Credenciais inválidas"}), 401
    
    access_token = create_access_token(
        identity=str(admin.id),
        additional_claims={"role": admin.role}
    )
    
    # Registrar log de login
    registrar_log(admin.id, 'LOGIN')
    
    return jsonify(access_token=access_token), 200

def forgot_password():
    data = request.get_json()
    admin = Admin.query.filter_by(email=data.get('email')).first()
    
    if admin:
        # Gera token seguro
        admin.reset_token = secrets.token_urlsafe(32)
        admin.reset_token_exp = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Registrar log
        registrar_log(admin.id, 'SOLICITACAO_RESET_SENHA')
        
        # Envia email
        try:
            msg = Message(
                subject="Recuperação de Senha",
                sender="wecemailtest@gmail.com",
                recipients=[admin.email],
                body=f"""Para redefinir sua senha, use o seguinte token:
                {admin.reset_token}
                
                Ou acesse o link: http://sua-api/reset-password?token={admin.reset_token}
                """
            )
            mail.send(msg)
        except Exception as e:
            print(f"Erro ao enviar email: {str(e)}")
            return jsonify({"message": "Erro no servidor de email"}), 500
        
    return jsonify({
        "message": "Se o email estiver cadastrado, enviaremos um link de recuperação"
    }), 200

def reset_password():
    data = request.get_json()
    admin = Admin.query.filter_by(
        reset_token=data.get('reset_token'),
        email=data.get('email')  
    ).first()
    
    if not admin or admin.reset_token_exp < datetime.utcnow():
        return jsonify({"message": "Token inválido ou expirado"}), 400
    
    if not data.get('new_password'):
        return jsonify({"message": "Nova senha é obrigatória"}), 400
    
    admin.set_password(data['new_password'])
    admin.reset_token = None
    admin.reset_token_exp = None
    db.session.commit()
    
    # Registrar log
    registrar_log(admin.id, 'RESET_SENHA')
    
    return jsonify({"message": "Senha atualizada com sucesso"}), 200

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Admin.query.get(int(identity))

@jwt_required()
@role_required('admin')
def get_admins():
    admins = Admin.query.all()
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
    
    # Registrar log
    registrar_log(current_admin_id, f'CRIAR_ADMIN:{new_admin.id}')
    
    return jsonify(new_admin.to_dict()), 201

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
    
    # Registrar log
    registrar_log(current_admin_id, f'CRIAR_USER:{new_user.id}')
    
    return jsonify(new_user.to_dict()), 201

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
    
    # Registrar log
    registrar_log(current_admin_id, 'ATUALIZAR_ADMIN')
    
    return jsonify(admin.to_dict()), 200

@jwt_required()
@role_required('admin')
def get_users():
    users = Admin.query.filter_by(role='user').all()
    return jsonify([user.to_dict() for user in users]), 200

@jwt_required()
def update_user():
    current_user_id = int(get_jwt_identity())
    user = Admin.query.get(current_user_id)
    
    if user.role != 'user' and user.role != 'admin':
        return jsonify({"message": "Acesso negado"}), 403
        
    data = request.get_json()
    
    if 'email' in data:
        if Admin.query.filter(Admin.email == data['email'], Admin.id != current_user_id).first():
            return jsonify({"message": "Email já está em uso"}), 400
        user.email = data['email']
    
    if 'username' in data:
        user.username = data['username']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    
    # Registrar log
    registrar_log(current_user_id, 'ATUALIZAR_USER')
    
    return jsonify(user.to_dict()), 200

@jwt_required()
@role_required('user')
def upload_file():
    current_user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({"message": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Nome de arquivo vazio"}), 400

    allowed = current_app.config.get('ALLOWED_EXTENSIONS')
    filename = secure_filename(file.filename)
    
    if allowed:
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in allowed:
            return jsonify({"message": f"Extensão .{ext} não permitida"}), 400

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, filename)
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"message": f"Erro ao salvar arquivo: {str(e)}"}), 500

    # Registrar log
    registrar_log(current_user_id, f'UPLOAD:{filename}')
    
    return jsonify({
        "message": "Arquivo enviado com sucesso",
        "filename": filename,
        "path": save_path
    }), 201

# Nova função para listar logs
@jwt_required()
@role_required('admin')
def get_logs():
    logs = Log.query.order_by(Log.data_hora.desc()).all()
    return jsonify([log.to_dict() for log in logs]), 200