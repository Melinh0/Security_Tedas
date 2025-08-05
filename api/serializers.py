#api/serializers.py
from rest_framework import serializers
from .models import CustomUser, Log, UploadedFile, Patient, Exam
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import USER_ROLE_CHOICES, PROFESSIONAL_TYPE_CHOICES

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Senha do usuário (mínimo 8 caracteres)"
    )
    role = serializers.ChoiceField(  # Alterado para ChoiceField
        choices=USER_ROLE_CHOICES,
        help_text="Papel do usuário"
    )
    professional_type = serializers.ChoiceField(  # Alterado para ChoiceField
        choices=PROFESSIONAL_TYPE_CHOICES,
        required=False,
        allow_blank=True,
        help_text="Tipo de profissional (apenas para profissionais da saúde)"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'cpf', 'full_name', 
            'role', 'professional_type', 'password'
        ]
        extra_kwargs = {
            'cpf': {
                'help_text': "CPF do usuário (apenas números)"
            },
            'full_name': {
                'help_text': "Nome completo do usuário"
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
    
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        extra_kwargs = {
            'medical_record_number': {
                'help_text': "Número único do prontuário do paciente"
            }
        }

class ExamSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    dicom_url = serializers.SerializerMethodField()
    dicom_file = serializers.FileField(  # Novo campo para upload
        required=True,
        write_only=True,
        help_text="Arquivo DICOM a ser enviado",
        style={'base_template': 'file.html', 'input_type': 'file'}
    )
    
    class Meta:
        model = Exam
        fields = [
            'id', 'patient', 'patient_name', 'user', 'user_name', 
            'status', 'uploaded_at', 'updated_at', 'medical_notes',
            'dicom_url', 'dicom_file'  # Inclui o novo campo
        ]
    
    def get_dicom_url(self, obj):
        if obj.original_dicom:
            return obj.original_dicom.url
        return None
    
    def validate_dicom_file(self, value):
        if not value.name.lower().endswith(('.dcm', '.dicom')):
            raise serializers.ValidationError("Apenas arquivos DICOM são permitidos")
        return value