import logging

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from . import encryption

logger = logging.getLogger(__name__)


def _default_role():
    return encryption.encrypt('user')


def _default_role_index():
    return encryption.blind_index('user')


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('O username e obrigatorio.')
        username = str(username).strip()
        role = extra_fields.pop('role', 'user')
        email = extra_fields.pop('email', None)
        user = self.model(
            username=encryption.encrypt(username),
            username_index=encryption.blind_index(username),
            role=encryption.encrypt(role),
            role_index=encryption.blind_index(role),
            email=encryption.encrypt(email) if email else None,
            email_index=encryption.blind_index(email) if email else None,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        return self._create_user(username, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username_index=encryption.blind_index(username))


class User(AbstractBaseUser, PermissionsMixin):
    username = models.TextField()
    username_index = models.CharField(max_length=64, unique=True, editable=False)
    email = models.TextField(null=True, blank=True)
    email_index = models.CharField(
        max_length=64, unique=True, null=True, blank=True, editable=False
    )
    role = models.TextField(default=_default_role)
    role_index = models.CharField(max_length=64, default=_default_role_index, editable=False)
    avatar = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        try:
            return self.get_username()
        except Exception:
            return f'User#{self.pk}'

    def get_username(self):
        return encryption.decrypt(self.username)

    @property
    def role_plain(self):
        return encryption.decrypt(self.role)

    @property
    def email_plain(self):
        return encryption.decrypt(self.email)

    @property
    def is_admin(self):
        return self.is_superuser or self.role_plain == 'admin'

    def set_username(self, username):
        username = str(username).strip()
        self.username = encryption.encrypt(username)
        self.username_index = encryption.blind_index(username)

    def set_role(self, role):
        self.role = encryption.encrypt(role)
        self.role_index = encryption.blind_index(role)

    def set_email(self, email):
        if email:
            self.email = encryption.encrypt(email)
            self.email_index = encryption.blind_index(email)
        else:
            self.email = None
            self.email_index = None


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('REGISTER', 'Cadastro'),
        ('LOGIN_SUCCESS', 'Login bem-sucedido'),
        ('LOGIN_FAILED', 'Login falhou'),
        ('LOGOUT', 'Logout'),
        ('TOKEN_REFRESH', 'Refresh de token'),
        ('ACCESS', 'Acesso a API'),
        ('ACCESS_DENIED', 'Acesso negado'),
        ('ACCESS_THROTTLED', 'Rate limit atingido'),
        ('REVEAL_PII', 'Revelacao de dados pessoais'),
        ('USER_CREATED', 'Usuario criado'),
        ('UPLOAD', 'Upload de arquivo'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs'
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    method = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=256, blank=True, default='')
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    detail = models.CharField(max_length=500, blank=True, default='')
    subject_enc = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['-timestamp', 'action'])]

    def __str__(self):
        return f'{self.action} @ {self.timestamp:%Y-%m-%d %H:%M:%S}'

    @property
    def subject_plain(self):
        return encryption.decrypt(self.subject_enc)
