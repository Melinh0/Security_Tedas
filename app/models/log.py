#app/models/log.py
from app import db
from datetime import datetime
from app.models.admin import Admin

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)  
    acao = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        # Tenta encontrar o usuário, mesmo se foi deletado
        user = Admin.query.get(self.usuario_id)
        if user:
            username = user.username
            email = user.email
        else:
            username = "Usuário deletado"
            email = ""

        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'acao': self.acao,
            'data_hora': self.data_hora.isoformat(),
            'username': username,
            'email': email
        }