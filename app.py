from flask import Flask, jsonify, request, make_response
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, timezone
import logging
from cryptography.fernet import Fernet

# Configuração do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Geração de chave de criptografia (deve ser armazenada de forma segura)
key = Fernet.generate_key()
cipher = Fernet(key)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta'

# Simulação de banco de dados de usuários
users_db = {
    'alice': {
        'password': generate_password_hash('senha_alice'),
        'roles': ['admin']
    },
    'bob': {
        'password': generate_password_hash('senha_bob'),
        'roles': ['user']
    }
}

def encrypt_data(data):
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data):
    return cipher.decrypt(data.encode()).decode()

# Função para verificar o token JWT e os papéis do usuário
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            logging.warning("Token ausente")
            return jsonify({'message': 'Token ausente!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users_db.get(data['username'])
            if not current_user:
                logging.warning("Usuário não encontrado")
                return jsonify({'message': 'Usuário não encontrado!'}), 401
        except jwt.ExpiredSignatureError:
            logging.warning("Token expirado")
            return jsonify({'message': 'Token expirado!'}), 401
        except jwt.InvalidTokenError:
            logging.warning("Token inválido")
            return jsonify({'message': 'Token inválido!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def requires_role(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            user_roles = current_user.get('roles', [])
            if any(role in required_roles for role in user_roles):
                return f(current_user, *args, **kwargs)
            else:
                logging.warning("Permissão negada")
                return jsonify({'message': 'Permissão negada!'}), 403
        return decorated_function
    return decorator

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        logging.warning("Credenciais inválidas")
        return make_response('Credenciais inválidas!', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = users_db.get(auth.username)
    if not user or not check_password_hash(user['password'], auth.password):
        logging.warning("Credenciais incorretas para o usuário: %s", auth.username)
        return make_response('Credenciais inválidas!', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    token = jwt.encode({
        'username': auth.username,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    encrypted_token = encrypt_data(token)
    logging.info("Token gerado para o usuário: %s", auth.username)
    return jsonify({'token': encrypted_token})

@app.route('/admin', methods=['GET'])
@token_required
@requires_role(['admin'])
def admin_route(current_user):
    logging.info("Acesso de admin por: %s", current_user)
    return jsonify({'message': 'Bem-vindo, admin!'})

@app.route('/user', methods=['GET'])
@token_required
@requires_role(['user', 'admin'])
def user_route(current_user):
    logging.info("Acesso de usuário por: %s", current_user)
    return jsonify({'message': 'Bem-vindo, usuario'})

@app.route('/public', methods=['GET'])
def public_route():
    logging.info("Acesso à rota pública")
    return jsonify({'message': 'Bem-vindo a rota publica'})

if __name__ == '__main__':
    logging.info("Iniciando o servidor")
    app.run(debug=True)