from django.core.management.base import BaseCommand

from api.encryption import generate_key


class Command(BaseCommand):
    help = 'Gera uma nova chave Fernet para ENCRYPTION_KEY (guarde como segredo do admin).'

    def handle(self, *args, **options):
        key = generate_key()
        self.stdout.write(self.style.SUCCESS(key))
        self.stdout.write(
            '\nAdicione ao arquivo .env:\n'
            f'ENCRYPTION_KEY={key}\n'
            '\nAVISO: quem possui esta chave condecriptar todos os dados pessoais. '
            'Nao a commite no repositorio.'
        )
