from rest_framework import serializers
from .models import Paciente

class PacienteSerializer(serializers.ModelSerializer):
    medical_info = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Paciente
        fields = '__all__'
        extra_kwargs = {
            'full_name': {'required': True},
            'birth_date': {'required': True},
        }