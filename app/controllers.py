from .models import User
from .__init__ import db

def create_default_admin():
    if not User.query.filter_by(username='yago').first():
        admin = User(username='yago', role='admin')
        admin.set_password('123')
        db.session.add(admin)
        db.session.commit()
