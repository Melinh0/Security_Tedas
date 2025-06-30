from django.apps import AppConfig
from django.db.utils import ProgrammingError, OperationalError
import logging

logger = logging.getLogger(__name__)

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    _users_created = False
    
    def ready(self):
        if not self._users_created:
            self._create_default_users()
    
    def _create_default_users(self):
        """Cria usuários padrão de forma segura"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Verifica se a tabela existe
            if not self._table_exists(User._meta.db_table):
                return
                
            self._create_admin_user(User)
            self._create_regular_user(User)
            
            self._users_created = True
            
        except (ProgrammingError, OperationalError) as e:
            logger.debug(f"Database not ready: {e}")
        except Exception as e:
            logger.error(f"Error creating default users: {e}")

    def _table_exists(self, table_name):
        from django.db import connection
        return table_name in connection.introspection.table_names()
    
    def _create_admin_user(self, User):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin',
                role='admin'
            )
            logger.info("Admin user created")
    
    def _create_regular_user(self, User):
        if not User.objects.filter(username='user').exists():
            User.objects.create_user(
                username='user',
                email='user@example.com',
                password='user',
                role='user'
            )
            logger.info("Regular user created")