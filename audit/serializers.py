from rest_framework import serializers
from .models import Registro

class RegistroSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Registro
        fields = ['id', 'profissional', 'action', 'timestamp', 'username', 'email', 'ip_address', 'success']
    
    def get_username(self, obj):
        return obj.profissional.username if obj.profissional else "Usuário deletado"
    
    def get_email(self, obj):
        return obj.profissional.email if obj.profissional else ""