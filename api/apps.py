#api/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging

logger = logging.getLogger(__name__)

def create_default_users(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Cria admin se não existir
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin',
                cpf='00000000000',
                full_name='Administrador Padrão',
                role='admin'
            )
            logger.info(f"Admin user created: {admin.username}")
        
        # Cria pesquisador padrão
        if not User.objects.filter(username='researcher').exists():
            researcher = User.objects.create_user(
                username='researcher',
                email='researcher@example.com',
                password='researcher',
                cpf='11111111111',
                full_name='Pesquisador Padrão',
                role='researcher'
            )
            logger.info(f"Researcher user created: {researcher.username}")
        
        # Cria profissional de saúde padrão
        if not User.objects.filter(username='doctor').exists():
            doctor = User.objects.create_user(
                username='doctor',
                email='doctor@example.com',
                password='doctor',
                cpf='22222222222',
                full_name='Médico Padrão',
                role='health_professional',
                professional_type='doctor'
            )
            logger.info(f"Health professional created: {doctor.username}")
            
    except Exception as e:
        logger.error(f"Error creating default users: {e}")

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        # Registra o sinal para criar usuários após migrações
        post_migrate.connect(create_default_users, sender=self)