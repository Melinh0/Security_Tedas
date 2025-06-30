from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import secrets
from django.core.mail import send_mail
from django.conf import settings
import os

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='user'):
        if not email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            role=role
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(max_length=120, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_exp = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def set_password(self, password):
        super().set_password(password)
        
    def check_password(self, password):
        return super().check_password(password)
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_exp = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        return self.reset_token
        
    def send_reset_email(self):
        try:
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

class Log(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def create_log(cls, user, action):
        cls.objects.create(user=user, action=action)
    
    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"

class UploadedFile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file.name
    
    def filename(self):
        return os.path.basename(self.file.name)