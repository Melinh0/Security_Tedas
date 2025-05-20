from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flasgger import Swagger

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Importar modelos ANTES de criar o banco
    from app.models.admin import Admin
    from app.controllers.admin_controller import user_lookup_callback
    
    # Inicializa extensões
    db.init_app(app)
    jwt.init_app(app)
    
    # Registra o user loader
    jwt.user_lookup_loader(user_lookup_callback)
    
    # Configuração do Swagger
    Swagger(app, template_file='swagger/admin_swagger.yaml')
    
    # Cria as tabelas e usuário admin padrão
    with app.app_context():
        db.create_all()
        
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(username='admin')
            default_admin.set_password('admin')
            db.session.add(default_admin)
            db.session.commit()
    
    # Registra blueprints
    from app.routes import admin_bp
    app.register_blueprint(admin_bp)
    
    return app