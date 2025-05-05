from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from .auth import auth_bp
from .views import view_bp
from .controllers import create_default_admin

# Declarar db globalmente
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Inicializando db, migrate e jwt
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    Swagger(app)

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(view_bp)

    with app.app_context():
        db.create_all()  # Criando as tabelas
        create_default_admin()

    return app
