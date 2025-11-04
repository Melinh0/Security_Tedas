from django.db import models
import hashlib
import base64
from cryptography.fernet import Fernet

def get_encryption_key():
    from django.conf import settings
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:32]

class Paciente(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    _medical_info = models.TextField(db_column='medical_info', blank=True, null=True)

    def __str__(self):
        return self.full_name

    @property
    def medical_info(self):
        if self._medical_info:
            key = base64.urlsafe_b64encode(get_encryption_key())
            fernet = Fernet(key)
            return fernet.decrypt(self._medical_info.encode()).decode()
        return None
    
    @medical_info.setter
    def medical_info(self, value):
        key = base64.urlsafe_b64encode(get_encryption_key())
        fernet = Fernet(key)
        self._medical_info = fernet.encrypt(value.encode()).decode()