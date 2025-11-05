from rest_framework import serializers
from .models import ProfissionalSaude
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data

class ProfissionalSaudeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    cpf = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = ProfissionalSaude
        fields = [
            'id', 'username', 'email', 'cpf', 'full_name', 
            'role', 'professional_type', 'password',
            'date_joined', 'last_modified'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'full_name': {'required': True},
        }
    
    def create(self, validated_data):
        cpf = validated_data.pop('cpf')
        password = validated_data.pop('password')
        user = ProfissionalSaude.objects.create_user(
            **validated_data,
            password=password
        )
        user.cpf = cpf
        user.save()
        return user

class AdminCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    cpf = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = ProfissionalSaude
        fields = ['username', 'email', 'cpf', 'full_name', 'password']
    
    def create(self, validated_data):
        cpf = validated_data.pop('cpf')
        password = validated_data.pop('password')
        user = ProfissionalSaude.objects.create_user(
            **validated_data,
            password=password,
            role='admin'
        )
        user.cpf = cpf
        user.save()
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reset_token = serializers.CharField(required=False)
    new_password = serializers.CharField(required=False, write_only=True)
    
    # REMOVA a validação problemática do email
    # def validate_email(self, value):
    #     if not ProfissionalSaude.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("Email não cadastrado")
    #     return value

class AdminCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    cpf = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = ProfissionalSaude
        fields = ['username', 'email', 'cpf', 'full_name', 'password']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'full_name': {'required': True},
        }
    
    def create(self, validated_data):
        cpf = validated_data.pop('cpf')
        password = validated_data.pop('password')
        user = ProfissionalSaude.objects.create_user(
            **validated_data,
            password=password,
            role='admin'
        )
        user.cpf = cpf
        user.save()
        return user