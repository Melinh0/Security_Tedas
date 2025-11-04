from django.db import models
import hashlib
import base64
from cryptography.fernet import Fernet
from .utils import encrypt_file, decrypt_file

def get_encryption_key():
    from django.conf import settings
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:32]

class FatiaTomografia(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Enviado'),
        ('segmentation_in_progress', 'Em Segmentação'),
        ('segmented', 'Segmentado'),
        ('error', 'Erro'),
    )
    
    id = models.AutoField(primary_key=True)
    paciente = models.ForeignKey('patients.Paciente', on_delete=models.CASCADE, related_name='fatias_tomografia')
    profissional = models.ForeignKey(
        'accounts.ProfissionalSaude', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='fatias_tomografia'
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
    segmentation_path = models.CharField(max_length=255, blank=True, null=True)
    mask_path = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='uploaded')
    _medical_notes = models.TextField(db_column='medical_notes', blank=True, null=True)

    def __str__(self):
        return f"Exame {self.id} - {self.paciente.full_name}"
    
    @property
    def medical_notes(self):
        if self._medical_notes:
            key = base64.urlsafe_b64encode(get_encryption_key())
            fernet = Fernet(key)
            return fernet.decrypt(self._medical_notes.encode()).decode()
        return None
    
    @medical_notes.setter
    def medical_notes(self, value):
        key = base64.urlsafe_b64encode(get_encryption_key())
        fernet = Fernet(key)
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