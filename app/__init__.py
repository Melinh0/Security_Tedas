#__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configurações do Swagger
    app.config['SWAGGER'] = {
        'swagger': '2.0',
        'info': {
            'title': 'API com JWT',
            'version': '1.0.0',
        },
        'securityDefinitions': {
            'jwt_token': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Bearer token JWT'
            }
        },
        'security': [{'jwt_token': []}]  # Exige JWT para todas as rotas
    }

    # Inicializando o Swagger
    swagger = Swagger(app)

    # Importações adiadas para evitar importação circular
    from .auth import auth_bp
    from .views import view_bp
    from .controllers import create_default_admin

    app.register_blueprint(auth_bp)
    app.register_blueprint(view_bp)

    with app.app_context():
        db.create_all()
        create_default_admin()

    return app
