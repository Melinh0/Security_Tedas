from flask import Flask
from app.controllers.user_controller import user_bp
from flasgger import Swagger
import logging

# Configuração do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta'

# Inicializa o Swagger
swagger = Swagger(app)

# Registro das rotas
def register_routes(app):
    app.register_blueprint(user_bp, url_prefix='/api')

if __name__ == '__main__':
    logging.info("Iniciando o servidor")
    app.run(debug=True)
