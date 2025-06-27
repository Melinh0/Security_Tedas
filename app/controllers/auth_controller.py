# app/controllers/auth_controller.py
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from flask_mail import Message
from app.models.admin import Admin
from app.models.log import Log
from app import db, mail
from datetime import datetime, timedelta
import secrets
from app import jwt

def registrar_log(usuario_id, acao):
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
    
    registrar_log(admin.id, 'LOGIN')
    return jsonify(access_token=access_token), 200

def forgot_password():
    data = request.get_json()
    admin = Admin.query.filter_by(email=data.get('email')).first()
    
    if admin:
        admin.reset_token = secrets.token_urlsafe(32)
        admin.reset_token_exp = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        registrar_log(admin.id, 'SOLICITACAO_RESET_SENHA')
        
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
    
    registrar_log(admin.id, 'RESET_SENHA')
    return jsonify({"message": "Senha atualizada com sucesso"}), 200

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Admin.query.get(int(identity))