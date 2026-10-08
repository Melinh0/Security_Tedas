from django.core.management.base import BaseCommand, CommandError

from api import encryption
from api.models import User


class Command(BaseCommand):
    help = 'Cria um usuario administrador (role=admin) com dados pessoais criptografados.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--email', default=None)

    def handle(self, *args, **options):
        username = options['username']
        if User.objects.filter(username_index=encryption.blind_index(username)).exists():
            raise CommandError(f'Usuario "{username}" ja existe.')
        if len(options['password']) < 8:
            raise CommandError('A senha deve ter no minimo 8 caracteres.')

        user = User.objects.create_superuser(
            username=username,
            password=options['password'],
            email=options['email'],
            role='admin',
        )
        self.stdout.write(
            self.style.SUCCESS(f'Admin "{user.get_username()}" (id={user.pk}) criado.')
        )
