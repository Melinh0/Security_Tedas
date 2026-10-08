from django.core.management.base import BaseCommand, CommandError

from api import encryption
from api.models import User


class Command(BaseCommand):
    help = 'Descriptografa os dados pessoais de um usuario (requer ENCRYPTION_KEY do admin).'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username em texto puro')
        parser.add_argument(
            '--field', choices=['all', 'username', 'email', 'role'], default='all'
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(
                username_index=encryption.blind_index(options['username'])
            )
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{options["username"]}" nao encontrado.')

        field = options['field']
        data = {}
        if field in ('all', 'username'):
            data['username'] = user.get_username()
        if field in ('all', 'email'):
            data['email'] = user.email_plain
        if field in ('all', 'role'):
            data['role'] = user.role_plain

        for key, value in data.items():
            self.stdout.write(f'{key}: {value}')
