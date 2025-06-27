from flask import Blueprint
from app.controllers.auth_controller import login, forgot_password, reset_password
from app.controllers.admin_controller import get_admins, create_admin, update_admin, get_users, create_user, delete_admin, delete_user, get_logs
from app.controllers.user_controller import update_user, upload_file, list_files

admin_bp = Blueprint('admin', __name__)

# Rotas de autenticação
admin_bp.route('/login', methods=['POST'])(login)
admin_bp.route('/forgot-password', methods=['POST'])(forgot_password)
admin_bp.route('/reset-password', methods=['POST'])(reset_password)

# Rotas de administrador
admin_bp.route('/admins', methods=['GET'])(get_admins)
admin_bp.route('/admins', methods=['POST'])(create_admin)
admin_bp.route('/admins/me', methods=['PUT'])(update_admin)
admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])(delete_admin)
admin_bp.route('/users', methods=['GET'])(get_users)
admin_bp.route('/users', methods=['POST'])(create_user)
admin_bp.route('/users/<int:user_id>', methods=['DELETE'])(delete_user)
admin_bp.route('/logs', methods=['GET'])(get_logs)

# Rotas de usuário
admin_bp.route('/users/me', methods=['PUT'])(update_user)
admin_bp.route('/users/me/upload', methods=['POST'])(upload_file)
admin_bp.route('/files', methods=['GET'])(list_files)