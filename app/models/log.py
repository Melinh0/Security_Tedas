#app/models/log.py
from app import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    usuario = db.relationship('Admin', backref='logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'acao': self.acao,
            'data_hora': self.data_hora.isoformat(),
            'username': self.usuario.username,
            'email': self.usuario.email
        }