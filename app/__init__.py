# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

# Inicializa a instância do banco de dados
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuração do banco de dados
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Ajuste conforme necessário
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sua_chave_secreta'  # Defina uma chave secreta

    # Inicializa o banco de dados com o app
    db.init_app(app)
    
    # Inicializa o Swagger
    Swagger(app)
    
    # Importa as rotas
    from app.routes.routes import register_routes
    register_routes(app)
    
    return app
