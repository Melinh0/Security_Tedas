#api/serializers.py
from rest_framework import serializers
from .models import CustomUser, Log, UploadedFile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        # Gerar URL completa para redirecionamento
        request = self.context.get('request')
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        data['swagger_redirect'] = f"{protocol}://{host}/swagger/redirect/?token={data['access']}"
        return data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Senha do usuário (mínimo 8 caracteres)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password']
        extra_kwargs = {
            'username': {
                'help_text': "Nome de usuário único para login"
            },
            'email': {
                'help_text': "Endereço de email válido"
            },
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'}
            },
            'role': {
                'help_text': "Papel do usuário (admin ou user)"
            }
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email do usuário para redefinição de senha"
    )
    reset_token = serializers.CharField(
        required=False,
        help_text="Token de redefinição recebido por email"
    )
    new_password = serializers.CharField(
        required=False,
        style={'input_type': 'password'},
        help_text="Nova senha (mínimo 8 caracteres)"
    )
    
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
        extra_kwargs = {
            'action': {
                'help_text': "Ação registrada no log (ex: LOGIN, UPLOAD, RESET_SENHA)"
            },
            'timestamp': {
                'help_text': "Data e hora do registro no formato ISO 8601"
            },
            'username': {
                'help_text': "Nome do usuário que realizou a ação"
            },
            'email': {
                'help_text': "Email do usuário que realizou a ação"
            }
        }
    
    def get_username(self, obj):
        return obj.user.username if obj.user else "Usuário deletado"
    
    def get_email(self, obj):
        return obj.user.email if obj.user else ""

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(
        required=True,
        help_text="Arquivo a ser enviado",
        style={'base_template': 'file.html', 'input_type': 'file'}
    )

class FileListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    modified = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    exists = serializers.SerializerMethodField()  
    
    class Meta:
        model = UploadedFile
        fields = ['user_id', 'name', 'size', 'modified', 'type', 'exists']
        extra_kwargs = {
            'name': {'help_text': "Nome do arquivo"},
            'size': {'help_text': "Tamanho do arquivo em bytes"},
            'modified': {'help_text': "Data de modificação em timestamp Unix"},
            'type': {'help_text': "Extensão do arquivo"},
            'exists': {'help_text': "Indica se o arquivo físico existe"}
        }
    
    def get_name(self, obj):
        return obj.filename()
    
    def get_size(self, obj):
        try:
            return obj.file.size
        except (FileNotFoundError, OSError):
            return 0  
    
    def get_modified(self, obj):
        try:
            return obj.uploaded_at.timestamp()
        except (FileNotFoundError, OSError):
            return None
    
    def get_type(self, obj):
        try:
            name = obj.filename()
            return name.split('.')[-1].lower() if '.' in name else 'unknown'
        except (FileNotFoundError, OSError):
            return 'deleted'
    
    def get_exists(self, obj):
        return obj.exists()  