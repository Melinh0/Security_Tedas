#api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from .models import Registro, Paciente, FatiaTomografia
from .serializers import (
    CustomTokenObtainPairSerializer, 
    ProfissionalSaudeSerializer, 
    PasswordResetSerializer,
    RegistroSerializer,
    PacienteSerializer,
    FatiaTomografiaSerializer,
)
from .permissions import RoleRequired
from django.shortcuts import get_object_or_404
import os
import magic
import tempfile
from django.core.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import hashlib

ProfissionalSaude = get_user_model()

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @swagger_auto_schema(
        operation_summary="Autenticar usuário",
        operation_description="Autentica um usuário com base nas credenciais fornecidas e retorna tokens de acesso.",
        responses={
            200: openapi.Response(
                description="Autenticação bem-sucedida",
                schema=CustomTokenObtainPairSerializer
            ),
            401: "Credenciais inválidas"
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = ProfissionalSaude.objects.get(username=request.data['username'])
            Registro.criar_registro(user, 'LOGIN', request)
        return response

class ForgotPasswordView(APIView):
    @swagger_auto_schema(
        operation_summary="Solicitar redefinição de senha",
        operation_description="Solicita a redefinição de senha para o email fornecido. Um token será enviado para o email do usuário.",
        request_body=PasswordResetSerializer,
        responses={
            200: openapi.Response(
                description="Solicitação processada",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: "Erro no servidor de email"
        }
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = ProfissionalSaude.objects.get(email=email)
        token = user.generate_reset_token()
        
        if user.send_reset_email():
            Registro.criar_registro(user, 'SOLICITACAO_RESET_SENHA', request, success=True)
            return Response({"message": "Se o email estiver cadastrado, enviaremos um link de recuperação"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Erro no servidor de email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):
    @swagger_auto_schema(
        operation_summary="Redefinir senha",
        operation_description="Redefine a senha do usuário usando o token recebido por email.",
        request_body=PasswordResetSerializer,
        responses={
            200: openapi.Response(
                description="Senha redefinida com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Token inválido ou expirado"
        }
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()        
        new_password = serializer.validated_data['new_password']
        
        user = get_object_or_404(
            ProfissionalSaude, 
            email=email, 
            reset_token=hashed_token,
            reset_token_exp__gte=timezone.now()
        )        
        if user.reset_token_exp < timezone.now():
            return Response({"message": "Token inválido ou expirado"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_exp = None
        user.save()
        
        Registro.criar_registro(user, 'RESET_SENHA', request, success=True)
        return Response({"message": "Senha atualizada com sucesso"}, status=status.HTTP_200_OK)

class UserListView(generics.ListCreateAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return ProfissionalSaude.objects.all()
        return ProfissionalSaude.objects.filter(id=self.request.user.id)
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            user_id = response.data['id']
            Registro.criar_registro(request.user, f'CRIAR_USER:{user_id}', request, success=True)
        return response
    
    @swagger_auto_schema(
        operation_summary="Listar usuários",
        operation_description="Lista todos os usuários cadastrados. Apenas administradores podem acessar.",
        responses={200: ProfissionalSaudeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Criar novo usuário",
        operation_description="Cria um novo usuário no sistema. Apenas administradores podem executar esta ação.",
        request_body=ProfissionalSaudeSerializer,
        responses={201: ProfissionalSaudeSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return ProfissionalSaude.objects.all()
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            Registro.criar_registro(request.user, 'ATUALIZAR_USER', request, success=True)
        return response
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({"message": "Você não pode deletar a si mesmo"}, status=status.HTTP_400_BAD_REQUEST)
        if user.username == 'admin':
            return Response({"message": "Não é permitido deletar o admin padrão"}, status=status.HTTP_400_BAD_REQUEST)
        if user.username == 'user':
            return Response({"message": "Não é permitido deletar o usuário padrão"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = user.id
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            Registro.criar_registro(request.user, f'DELETE_USER:{user_id}', request, success=True)
        return response
    
    @swagger_auto_schema(
        operation_summary="Obter detalhes do usuário",
        operation_description="Obtém detalhes de um usuário específico pelo ID ou use 'me' para obter informações do usuário autenticado.",
        responses={200: ProfissionalSaudeSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Atualizar usuário",
        operation_description="Atualiza as informações de um usuário existente. Apenas administradores podem executar esta ação.",
        request_body=ProfissionalSaudeSerializer,
        responses={200: ProfissionalSaudeSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Excluir usuário",
        operation_description="Exclui um usuário do sistema. Não é possível excluir usuários padrão (admin, user) ou a si mesmo.",
        responses={204: "Usuário excluído com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class AdminListView(generics.ListCreateAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return ProfissionalSaude.objects.filter(role='admin')
    
    @swagger_auto_schema(
        operation_summary="Listar administradores",
        operation_description="Lista todos os administradores cadastrados no sistema. Apenas administradores podem acessar.",
        responses={200: ProfissionalSaudeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Criar novo administrador",
        operation_description="Cria um novo usuário com perfil de administrador. Apenas administradores podem executar esta ação.",
        request_body=ProfissionalSaudeSerializer,
        responses={201: ProfissionalSaudeSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        return ProfissionalSaude.objects.filter(role='admin')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crie o usuário usando o UserManager
        user = ProfissionalSaude.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            role='admin'
        )
        
        # Agora temos um ID válido para registrar no log
        Registro.criar_registro(request.user, f'CRIAR_ADMIN:{user.id}', request, success=True)
        
        # Serialize a resposta
        response_serializer = ProfissionalSaudeSerializer(user)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return ProfissionalSaude.objects.filter(role='admin')
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    @swagger_auto_schema(
        operation_summary="Obter detalhes do administrador",
        operation_description="Obtém detalhes de um administrador específico pelo ID ou use 'me' para obter informações do administrador autenticado.",
        responses={200: ProfissionalSaudeSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Atualizar administrador",
        operation_description="Atualiza as informações de um administrador existente. Apenas administradores podem executar esta ação.",
        request_body=ProfissionalSaudeSerializer,
        responses={200: ProfissionalSaudeSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Excluir administrador",
        operation_description="Exclui um administrador do sistema. Não é possível excluir o administrador padrão (admin) ou a si mesmo.",
        responses={204: "Administrador excluído com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            Registro.criar_registro(request.user, 'ATUALIZAR_ADMIN', request, success=True)
        return response
    
    def destroy(self, request, *args, **kwargs):
        admin = self.get_object()
        
        # Prevenções de deleção
        if admin == request.user:
            return Response({"message": "Você não pode deletar a si mesmo"}, status=status.HTTP_400_BAD_REQUEST)
        if admin.username == 'admin':
            return Response({"message": "Não é permitido deletar o admin padrão"}, status=status.HTTP_400_BAD_REQUEST)
        
        admin_id = admin.id
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            Registro.criar_registro(request.user, f'DELETE_ADMIN:{admin_id}', request, success=True)
        return response

class RegistroListView(generics.ListAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return Registro.objects.all().order_by('-timestamp')
    
    @swagger_auto_schema(
        operation_summary="Listar registros do sistema",
        operation_description="Lista todos os registros de atividades do sistema. Apenas administradores podem acessar.",
        responses={200: RegistroSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
class PacienteListView(generics.ListCreateAPIView):
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Paciente.objects.all()

    @swagger_auto_schema(
        operation_summary="Listar pacientes",
        operation_description="Lista todos os pacientes cadastrados. Acesso para administradores e profissionais de saúde.",
        responses={200: PacienteSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar novo paciente",
        operation_description="Cria um novo registro de paciente. Acesso para administradores e profissionais de saúde.",
        request_body=PacienteSerializer,
        responses={201: PacienteSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PacienteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Paciente.objects.all()

    @swagger_auto_schema(
        operation_summary="Detalhes do paciente",
        operation_description="Obtém detalhes de um paciente específico pelo ID.",
        responses={200: PacienteSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar paciente",
        operation_description="Atualiza as informações de um paciente existente.",
        request_body=PacienteSerializer,
        responses={200: PacienteSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir paciente",
        operation_description="Exclui permanentemente um registro de paciente.",
        responses={204: "Paciente excluído com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class FatiaTomografiaListView(generics.ListCreateAPIView):
    serializer_class = FatiaTomografiaSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    parser_classes = [MultiPartParser]  # Aceita upload de arquivos
    
    def get_required_roles(self):
        if self.request.method == 'POST':
            return ['health_professional']
        return ['admin', 'health_professional', 'researcher']
    
    def get_queryset(self):
        user = self.request.user
        queryset = FatiaTomografia.objects.all()
        
        if user.role == 'researcher':
            queryset = queryset.filter(status='segmented')
        elif user.role == 'health_professional':
            queryset = queryset.filter(profissional=user)
        
        return queryset

    @swagger_auto_schema(
        operation_summary="Listar fatias de tomografia",
        operation_description=(
            "Lista fatias de tomografia de acordo com o perfil do usuário:\n"
            "- Administradores: Todos os exames\n"
            "- Profissionais de saúde: Apenas seus próprios exames\n"
            "- Pesquisadores: Apenas exames anonimizados (segmented)"
        ),
        responses={200: FatiaTomografiaSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar nova fatia de tomografia",
        operation_description=(
            "Cria uma nova fatia de tomografia com upload de arquivo DICOM\n\n"
            "**Campos obrigatórios:**\n"
            "- `paciente`: ID do paciente associado\n"
            "- `dicom_file`: Arquivo DICOM a ser enviado\n\n"
            "**Campos opcionais:**\n"
            "- `medical_notes`: Notas médicas sobre o exame\n"
            "- `status`: Status inicial do exame (padrão: 'uploaded')"
        ),
        request_body=FatiaTomografiaSerializer,
        responses={
            201: FatiaTomografiaSerializer,
            400: "Erro de validação",
            403: "Permissão negada"
        }
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificação de segurança do arquivo
        dicom_file = serializer.validated_data['dicom_file']
        temp_file = None
        
        try:
            # Criar arquivo temporário para análise
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in dicom_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Verificar tipo MIME
            mime = magic.Magic(mime=True)
            real_mime = mime.from_file(temp_file_path)
            
            if real_mime not in settings.DICOM_ALLOWED_MIME_TYPES:
                raise ValidationError("Tipo de arquivo inválido. Apenas DICOM é permitido")
            
            # Criar o exame
            fatia_tomografia = FatiaTomografia(
                paciente=serializer.validated_data['paciente'],
                profissional=request.user,
                status='uploaded'
            )
            
            if 'medical_notes' in serializer.validated_data:
                fatia_tomografia.medical_notes = serializer.validated_data['medical_notes']
            
            fatia_tomografia.save()
            
            # Salvar o arquivo DICOM
            filename = f"exam_{fatia_tomografia.id}_{dicom_file.name}"
            fatia_tomografia.original_dicom.save(filename, dicom_file)
            fatia_tomografia.save()
            
            Registro.criar_registro(request.user, f'UPLOAD_DICOM:{filename}', request, success=True)
            headers = self.get_success_headers(serializer.data)
            return Response(FatiaTomografiaSerializer(fatia_tomografia).data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            Registro.criar_registro(request.user, f'UPLOAD_DICOM_FAILED:{dicom_file.name}', request, success=False)
            return Response({"message": f"Erro no processamento: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if temp_file:
                os.unlink(temp_file_path)

class FatiaTomografiaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FatiaTomografiaSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    
    def get_required_roles(self):
        fatia_tomografia = self.get_object()
        
        # Apenas o criador do exame ou admin pode editar/excluir
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.role == 'admin':
                return True
            return fatia_tomografia.profissional == self.request.user
        
        # Visualização permitida para pesquisadores (apenas leitura)
        return ['admin', 'health_professional', 'researcher']
    
    def get_queryset(self):
        return FatiaTomografia.objects.all()

    @swagger_auto_schema(
        operation_summary="Detalhes da fatia de tomografia",
        operation_description=(
            "Obtém detalhes de uma fatia de tomografia específica pelo ID.\n"
            "Permissões:\n"
            "- Administradores: Acesso completo\n"
            "- Profissional de saúde: Apenas seus próprios exames\n"
            "- Pesquisadores: Apenas exames anonimizados"
        ),
        responses={200: FatiaTomografiaSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar fatia de tomografia",
        operation_description=(
            "Atualiza as informações de uma fatia de tomografia existente.\n"
            "Permissões:\n"
            "- Apenas administradores ou o profissional de saúde que criou o exame"
        ),
        request_body=FatiaTomografiaSerializer,
        responses={200: FatiaTomografiaSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir fatia de tomografia",
        operation_description=(
            "Exclui permanentemente um registro de fatia de tomografia.\n"
            "Permissões:\n"
            "- Apenas administradores ou o profissional de saúde que criou o exame"
        ),
        responses={204: "Fatia de tomografia excluída com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)