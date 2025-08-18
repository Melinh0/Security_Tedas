from rest_framework import serializers
from .models import ProfissionalSaude, Registro, Paciente, FatiaTomografia
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import USER_ROLE_CHOICES, PROFESSIONAL_TYPE_CHOICES

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data

class ProfissionalSaudeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Senha do usuário (mínimo 8 caracteres)"
    )
    role = serializers.ChoiceField(
        choices=USER_ROLE_CHOICES,
        help_text="Papel do usuário"
    )
    professional_type = serializers.ChoiceField(
        choices=PROFESSIONAL_TYPE_CHOICES,
        required=False,
        allow_blank=True,
        help_text="Tipo de profissional (apenas para profissionais da saúde)"
    )
    cpf = serializers.CharField(
        required=True,
        write_only=True,  # Opcional: depende se você quer retornar o CPF após criação
        help_text="CPF do usuário (apenas números)"
    )
    
    class Meta:
        model = ProfissionalSaude
        fields = [
            'id', 'username', 'email', 'cpf', 'full_name', 
            'role', 'professional_type', 'password',
            'date_joined', 'last_modified'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'cpf': {
                'help_text': "CPF do usuário (apenas números)"
            },
            'full_name': {
                'help_text': "Nome completo do usuário"
            },
            'date_joined': {
                'help_text': "Data de cadastro do usuário"
            },
            'last_modified': {
                'help_text': "Última atualização dos dados do usuário"
            }
        }
    
    def create(self, validated_data):
        cpf = validated_data.pop('cpf', None)
        user = super().create(validated_data)
        if cpf:
            user.cpf = cpf  # Usa o setter para criptografia
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
        if not ProfissionalSaude.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email não cadastrado")
        return value

class RegistroSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Registro
        fields = ['id', 'profissional', 'action', 'timestamp', 'username', 'email', 'ip_address', 'success']
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
            },
            'ip_address': {
                'help_text': "Endereço IP do usuário durante a ação"
            },
            'success': {
                'help_text': "Indica se a ação foi bem sucedida"
            }
        }
    
    def get_username(self, obj):
        return obj.profissional.username if obj.profissional else "Usuário deletado"
    
    def get_email(self, obj):
        return obj.profissional.email if obj.profissional else ""
    
class PacienteSerializer(serializers.ModelSerializer):
    medical_info = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Paciente
        fields = '__all__'

class FatiaTomografiaSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='paciente.full_name', read_only=True)
    user_name = serializers.CharField(source='profissional.full_name', read_only=True)
    dicom_url = serializers.SerializerMethodField()
    dicom_file = serializers.FileField(
        required=True,
        write_only=True,
        help_text="Arquivo DICOM a ser enviado",
        style={'base_template': 'file.html', 'input_type': 'file'}
    )
    
    class Meta:
        model = FatiaTomografia
        fields = [
            'id', 'paciente', 'patient_name', 'profissional', 'user_name', 
            'status', 'uploaded_at', 'updated_at', 'medical_notes',
            'dicom_url', 'dicom_file', 'segmentation_path', 'mask_path'
        ]
        extra_kwargs = {
            'segmentation_path': {
                'help_text': "Caminho para arquivo de segmentação"
            },
            'mask_path': {
                'help_text': "Caminho para arquivo de máscara"
            },
            'uploaded_at': {
                'help_text': "Data de envio do exame"
            },
            'updated_at': {
                'help_text': "Última atualização do exame"
            }
        }
    
    def get_dicom_url(self, obj):
        if obj.original_dicom:
            return obj.original_dicom.url
        return None
    
    def validate_dicom_file(self, value):
        if not value.name.lower().endswith(('.dcm', '.dicom')):
            raise serializers.ValidationError("Apenas arquivos DICOM são permitidos")
        return value