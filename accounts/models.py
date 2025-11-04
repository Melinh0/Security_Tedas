from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import secrets
from django.core.mail import send_mail
import hashlib
import base64
from cryptography.fernet import Fernet

def get_encryption_key():
    from django.conf import settings
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:32]

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        
        extra_fields.setdefault('role', 'user')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('role', 'admin')  
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(username, email, password, **extra_fields)

USER_ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('researcher', 'Pesquisador'),
    ('health_professional', 'Profissional da Saúde'),
)

PROFESSIONAL_TYPE_CHOICES = (
    ('doctor', 'Médico'),
    ('nutritionist', 'Nutricionista'),
    ('radiologist', 'Radiologista'),
    ('other', 'Outro'),
)

class ProfissionalSaude(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(max_length=120, unique=True)
    _cpf = models.CharField(max_length=255, db_column='cpf', blank=True, null=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default='health_professional')
    professional_type = models.CharField(
        max_length=20, 
        choices=PROFESSIONAL_TYPE_CHOICES, 
        blank=True, 
        null=True
    )
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_exp = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def cpf(self):
        if self._cpf:
            key = base64.urlsafe_b64encode(get_encryption_key())
            fernet = Fernet(key)
            return fernet.decrypt(self._cpf.encode()).decode()
        return None
    
    @cpf.setter
    def cpf(self, value):
        key = base64.urlsafe_b64encode(get_encryption_key())
        fernet = Fernet(key)
        self._cpf = fernet.encrypt(value.encode()).decode()

    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        self.reset_token = hashed_token
        self.reset_token_exp = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        return token
        
    def send_reset_email(self):
        try:
            from django.conf import settings
            send_mail(
                subject="Recuperação de Senha",
                message=f"""Para redefinir sua senha, use o seguinte token:
                {self.reset_token}
                
                Ou acesse o link: http://sua-api/reset-password?token={self.reset_token}
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.email],
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {str(e)}")
            return False