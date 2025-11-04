from django.db import models

class Registro(models.Model):
    profissional = models.ForeignKey(
        'accounts.ProfissionalSaude', 
        on_delete=models.SET_NULL, 
        null=True
    )
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=True)
    
    @classmethod
    def criar_registro(cls, profissional, action, request, success=True):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        cls.objects.create(
            profissional=profissional, 
            action=action, 
            ip_address=ip,
            success=success
        )
    
    def __str__(self):
        return f"{self.profissional} - {self.action} at {self.timestamp}"