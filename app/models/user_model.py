# app/models/user_model.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.Column(db.String(255), nullable=False, default='user')

    def __init__(self, username, password, roles=['user']):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.roles = ','.join(roles)  # Armazena os papéis como string separada por vírgula

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_user(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def create_user(cls, username, password, roles=['user']):
        if cls.get_user(username):
            return False
        new_user = cls(username=username, password=password, roles=roles)
        db.session.add(new_user)
        db.session.commit()
        return True

    @classmethod
    def update_password(cls, username, new_password):
        user = cls.get_user(username)
        if not user:
            return False
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True

    @classmethod
    def delete_user(cls, username):
        user = cls.get_user(username)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True
