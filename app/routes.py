#app/routes.py
from flask import Blueprint
from app.controllers.admin_controller import (
    login, 
    get_admins, 
    create_admin,  
    update_admin, 
    forgot_password, 
    reset_password, 
    get_users, 
    update_user,
    create_user, 
    upload_file,
    get_logs,
    delete_admin,  
    delete_user,
    list_files    
)

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

@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
def delete_admin_route(admin_id):
    return delete_admin(admin_id)

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    return delete_user(user_id)

@admin_bp.route('/users', methods=['GET'])
def get_users_route():
    return get_users()

@admin_bp.route('/users', methods=['POST'])
def create_user_route():
    return create_user()

@admin_bp.route('/users/me', methods=['PUT'])
def update_user_route():
    return update_user()

@admin_bp.route('/users/me/upload', methods=['POST'])
def upload_file_route():
    return upload_file()

@admin_bp.route('/logs', methods=['GET'])
def get_logs_route():
    return get_logs()

@admin_bp.route('/files', methods=['GET'])
def list_files_route():
    return list_files()