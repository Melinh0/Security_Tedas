import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def generate_key() -> str:
    return Fernet.generate_key().decode('ascii')


def _fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode('ascii')
    try:
        return Fernet(key)
    except ValueError as exc:
        raise ImproperlyConfigured('ENCRYPTION_KEY invalida (chave Fernet esperada).') from exc


def encrypt(value):
    if value is None or value == '':
        return value
    return _fernet().encrypt(str(value).encode('utf-8')).decode('ascii')


def decrypt(token):
    if token is None or token == '':
        return token
    if not isinstance(token, str):
        return token
    try:
        return _fernet().decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError) as exc:
        raise ImproperlyConfigured(
            'Falha ao descriptografar: ENCRYPTION_KEY incorreta ou dado corrompido.'
        ) from exc


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith('gAAAAA')


def blind_index(value) -> str:
    normalized = str(value).strip().lower().encode('utf-8')
    secret = settings.BLIND_INDEX_KEY.encode('utf-8')
    return hmac.new(secret, normalized, hashlib.sha256).hexdigest()
