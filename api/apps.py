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
                password='admin'
            )
            logger.info(f"Admin user created: {admin.username}")
        
        # Cria user regular se não existir
        if not User.objects.filter(username='user').exists():
            user = User.objects.create_user(
                username='user',
                email='user@example.com',
                password='user',
                role='user'
            )
            logger.info(f"Regular user created: {user.username}")
    except Exception as e:
        logger.error(f"Error creating default users: {e}")

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        # Registra o sinal para criar usuários após migrações
        post_migrate.connect(create_default_users, sender=self)