# app/controllers/user_controller.py
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.admin import Admin
from app.models.log import Log
from app import db
from app.utils.decorators import role_required
import os
from werkzeug.utils import secure_filename

def registrar_log(usuario_id, acao):
    novo_log = Log(usuario_id=usuario_id, acao=acao)
    db.session.add(novo_log)
    db.session.commit()

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
    user_folder = os.path.join(upload_folder, str(current_user_id))
    os.makedirs(user_folder, exist_ok=True)

    save_path = os.path.join(user_folder, filename)
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"message": f"Erro ao salvar arquivo: {str(e)}"}), 500

    registrar_log(current_user_id, f'UPLOAD:{filename}')
    return jsonify({
        "message": "Arquivo enviado com sucesso",
        "filename": filename,
        "path": save_path
    }), 201

@jwt_required()
def list_files():
    current_user_id = int(get_jwt_identity())
    user = Admin.query.get(current_user_id)
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(upload_folder):
        return jsonify({"message": "Pasta de uploads não existe"}), 404
    
    files = []
    
    if user.role == 'admin':
        for user_id in os.listdir(upload_folder):
            user_folder = os.path.join(upload_folder, user_id)
            if os.path.isdir(user_folder):
                for filename in os.listdir(user_folder):
                    filepath = os.path.join(user_folder, filename)
                    if os.path.isfile(filepath):
                        file_info = {
                            'user_id': int(user_id),
                            'name': filename,
                            'size': os.path.getsize(filepath),
                            'modified': os.path.getmtime(filepath),
                            'type': filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                        }
                        files.append(file_info)
    else:
        user_folder = os.path.join(upload_folder, str(current_user_id))
        if os.path.exists(user_folder):
            for filename in os.listdir(user_folder):
                filepath = os.path.join(user_folder, filename)
                if os.path.isfile(filepath):
                    file_info = {
                        'user_id': current_user_id,
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'modified': os.path.getmtime(filepath),
                        'type': filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                    }
                    files.append(file_info)
    
    if user.role == 'admin':
        registrar_log(current_user_id, 'LISTAR_ARQUIVOS_ADMIN')
    else:
        registrar_log(current_user_id, 'LISTAR_ARQUIVOS_USER')
    
    return jsonify(files), 200