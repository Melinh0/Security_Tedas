from rest_framework import serializers
from .models import CustomUser, Log, UploadedFile
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.CharField(required=False)
    new_password = serializers.CharField(required=False)
    
    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email não cadastrado")
        return value

class LogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Log
        fields = ['id', 'user', 'action', 'timestamp', 'username', 'email']
    
    def get_username(self, obj):
        return obj.user.username if obj.user else "Usuário deletado"
    
    def get_email(self, obj):
        return obj.user.email if obj.user else ""

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['user', 'uploaded_at']

class FileListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    modified = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = ['user_id', 'name', 'size', 'modified', 'type']
    
    def get_name(self, obj):
        return obj.filename()
    
    def get_size(self, obj):
        return obj.file.size
    
    def get_modified(self, obj):
        return obj.uploaded_at.timestamp()
    
    def get_type(self, obj):
        name = obj.filename()
        return name.split('.')[-1].lower() if '.' in name else 'unknown'