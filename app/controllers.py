#controllers.py
from .models import User
from . import db

def create_default_admin():
    if not User.query.filter_by(username='yago').first():
        user = User(username="yago")
        user.set_password("admin")
        db.session.add(user)
        db.session.commit()       
        db.session.add(user)
        db.session.commit()
