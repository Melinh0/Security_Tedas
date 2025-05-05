# app/services/user_service.py
from app.models.user_model import User

def create_user(username, password, roles=['user']):
    return User.create_user(username, password, roles)

def update_password(username, new_password):
    return User.update_password(username, new_password)

def delete_user(username):
    return User.delete_user(username)
