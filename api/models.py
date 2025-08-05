#api/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import secrets
from django.core.mail import send_mail
from django.conf import settings
import os
import hashlib
import base64
import logging
from cryptography.fernet import Fernet
from .utils import encrypt_file, decrypt_file

# Configure o logger
logger = logging.getLogger(__name__)

# Função para gerar chave de criptografia
def get_encryption_key():
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:32]

# Adicione estas escolhas no topo do arquivo
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

# Modifique a classe CustomUser
class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(max_length=120, unique=True)
    _cpf = models.CharField(max_length=255, db_column='cpf', blank=True, null=True)  # Campo criptografado
    full_name = models.CharField(max_length=255)  # Adicionado nome completo
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default='health_professional')
    professional_type = models.CharField(  # Novo campo
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

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def cpf(self):
        if self._cpf:
            fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
            return fernet.decrypt(self._cpf.encode()).decode()
        return None
    
    @cpf.setter
    def cpf(self, value):
        fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
        self._cpf = fernet.encrypt(value.encode()).decode()

    def set_password(self, password):
        super().set_password(password)
        
    def check_password(self, password):
        return super().check_password(password)
    
    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        self.reset_token = hashed_token
        self.reset_token_exp = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        return token
        
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
        try:
            return os.path.basename(self.file.name)
        except FileNotFoundError:
            return "Arquivo não encontrado"
    
    def exists(self):
        """Verifica se o arquivo físico existe"""
        try:
            return self.file.storage.exists(self.file.name)
        except Exception:
            return False
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.file and os.path.exists(self.file.path):
            encrypt_file(self.file.path)
    
    def read_decrypted(self):
        return decrypt_file(self.file.path)
    
    def get_file_content(self):
        try:
            return self.read_decrypted()
        except Exception as e:
            logger.error(f"Error decrypting file: {str(e)}")
            return None
    
class Patient(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    _medical_info = models.TextField(db_column='medical_info', blank=True, null=True)  # Campo criptografado
    medical_record_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.full_name

    @property
    def medical_info(self):
        if self._medical_info:
            fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
            return fernet.decrypt(self._medical_info.encode()).decode()
        return None
    
    @medical_info.setter
    def medical_info(self, value):
        fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
        self._medical_info = fernet.encrypt(value.encode()).decode()

class Exam(models.Model):
    EXAM_STATUS_CHOICES = (
        ('uploaded', 'Enviado'),
        ('segmentation_in_progress', 'Em Segmentação'),
        ('segmented', 'Segmentado'),
        ('error', 'Erro'),
    )
    
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='exams')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='exams'
    )
    original_dicom = models.FileField(
        upload_to='dicom/original/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Arquivo DICOM original"
    )
    anonymized_dicom = models.FileField(
        upload_to='dicom/anonymized/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Arquivo DICOM anonimizado"
    )
    segmentation_csv_path = models.CharField(max_length=255, blank=True, null=True)  # Segmentação CSV
    segmentation_svg_path = models.CharField(max_length=255, blank=True, null=True)  # Segmentação SVG
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=EXAM_STATUS_CHOICES, default='uploaded')
    _medical_notes = models.TextField(db_column='medical_notes', blank=True, null=True)  # Campo criptografado

    def __str__(self):
        return f"Exame {self.id} - {self.patient.full_name}"
    
    @property
    def medical_notes(self):
        if self._medical_notes:
            fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
            return fernet.decrypt(self._medical_notes.encode()).decode()
        return None
    
    @medical_notes.setter
    def medical_notes(self, value):
        fernet = Fernet(base64.urlsafe_b64encode(get_encryption_key()))
        self._medical_notes = fernet.encrypt(value.encode()).decode()
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Criptografar arquivos após salvar
        if is_new and self.original_dicom:
            encrypt_file(self.original_dicom.path)
        if self.anonymized_dicom:
            encrypt_file(self.anonymized_dicom.path)
    
    def get_original_dicom(self):
        if self.original_dicom:
            return decrypt_file(self.original_dicom.path)
        return None
    
    def get_anonymized_dicom(self):
        if self.anonymized_dicom:
            return decrypt_file(self.anonymized_dicom.path)
        return None