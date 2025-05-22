#app/routes.py
from flask import Blueprint
from app.controllers.admin_controller import login, get_admins, create_admin, update_admin, forgot_password, reset_password

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['POST'])
def login_route():
    return login()

@admin_bp.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    return forgot_password()

@admin_bp.route('/reset-password', methods=['POST'])
def reset_password_route():
    return reset_password()

@admin_bp.route('/admins', methods=['GET'])
def get_admins_route():
    return get_admins()

@admin_bp.route('/admins', methods=['POST'])
def create_admin_route():
    return create_admin()

@admin_bp.route('/admins/me', methods=['PUT'])
def update_admin_route():
    return update_admin()