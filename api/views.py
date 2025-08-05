#api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from .models import Log, UploadedFile, Patient, Exam
from .serializers import (
    CustomTokenObtainPairSerializer, 
    UserSerializer, 
    PasswordResetSerializer,
    LogSerializer,
    FileUploadSerializer,
    FileListSerializer,
    PatientSerializer,
    ExamSerializer,
    ExamCreateSerializer
)
from .permissions import RoleRequired
from django.shortcuts import get_object_or_404
import os
import magic
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import hashlib

User = get_user_model()

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
            user = User.objects.get(username=request.data['username'])
            Log.create_log(user, 'LOGIN')
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
        user = User.objects.get(email=email)
        token = user.generate_reset_token()
        
        if user.send_reset_email():
            Log.create_log(user, 'SOLICITACAO_RESET_SENHA')
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
            User, 
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
        
        Log.create_log(user, 'RESET_SENHA')
        return Response({"message": "Senha atualizada com sucesso"}, status=status.HTTP_200_OK)

class UserListView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            user_id = response.data['id']
            Log.create_log(request.user, f'CRIAR_USER:{user_id}')
        return response
    
    @swagger_auto_schema(
        operation_summary="Listar usuários",
        operation_description="Lista todos os usuários cadastrados. Apenas administradores podem acessar.",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Criar novo usuário",
        operation_description="Cria um novo usuário no sistema. Apenas administradores podem executar esta ação.",
        request_body=UserSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return User.objects.all()
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            Log.create_log(request.user, 'ATUALIZAR_USER')
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
            Log.create_log(request.user, f'DELETE_USER:{user_id}')
        return response
    
    @swagger_auto_schema(
        operation_summary="Obter detalhes do usuário",
        operation_description="Obtém detalhes de um usuário específico pelo ID ou use 'me' para obter informações do usuário autenticado.",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Atualizar usuário",
        operation_description="Atualiza as informações de um usuário existente. Apenas administradores podem executar esta ação.",
        request_body=UserSerializer,
        responses={200: UserSerializer}
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
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return User.objects.filter(role='admin')
    
    @swagger_auto_schema(
        operation_summary="Listar administradores",
        operation_description="Lista todos os administradores cadastrados no sistema. Apenas administradores podem acessar.",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Criar novo administrador",
        operation_description="Cria um novo usuário com perfil de administrador. Apenas administradores podem executar esta ação.",
        request_body=UserSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        return User.objects.filter(role='admin')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crie o usuário usando o UserManager
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            role='admin'
        )
        
        # Agora temos um ID válido para registrar no log
        Log.create_log(request.user, f'CRIAR_ADMIN:{user.id}')
        
        # Serialize a resposta
        response_serializer = UserSerializer(user)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return User.objects.filter(role='admin')
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    @swagger_auto_schema(
        operation_summary="Obter detalhes do administrador",
        operation_description="Obtém detalhes de um administrador específico pelo ID ou use 'me' para obter informações do administrador autenticado.",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Atualizar administrador",
        operation_description="Atualiza as informações de um administrador existente. Apenas administradores podem executar esta ação.",
        request_body=UserSerializer,
        responses={200: UserSerializer}
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
            Log.create_log(request.user, 'ATUALIZAR_ADMIN')
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
            Log.create_log(request.user, f'DELETE_ADMIN:{admin_id}')
        return response

class LogListView(generics.ListAPIView):
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
    def get_queryset(self):
        return Log.objects.all().order_by('-timestamp')
    
    @swagger_auto_schema(
        operation_summary="Listar logs do sistema",
        operation_description="Lista todos os logs de atividades do sistema. Apenas administradores podem acessar.",
        responses={200: LogSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class FileUploadView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Fazer upload de arquivo",
        operation_description="Realiza o upload de um arquivo associado ao usuário autenticado com verificação de segurança.",
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Arquivo a ser enviado (máx. 10MB)"
            )
        ],
        responses={
            201: openapi.Response(
                description="Arquivo enviado com sucesso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'filename': openapi.Schema(type=openapi.TYPE_STRING),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                        'exists': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: "Erro de validação ou arquivo suspeito",
            500: "Erro interno ao salvar"
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        
        # Sempre extraia a extensão, mesmo se ALLOWED_EXTENSIONS não estiver definido
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')

        # Verificar extensões permitidas
        if settings.ALLOWED_EXTENSIONS:
            if ext not in settings.ALLOWED_EXTENSIONS:
                return Response({"message": f"Extensão .{ext} não permitida"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verificação de segurança contra arquivos maliciosos
        try:
            # Criar arquivo temporário para análise
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Analisar o tipo MIME real do arquivo
            mime = magic.Magic(mime=True)
            real_mime = mime.from_file(temp_file_path)
            
            # Lista de tipos MIME perigosos
            dangerous_mimes = [
                'application/x-msdownload',  # Executáveis Windows
                'application/x-dosexec',      # Executáveis DOS
                'application/x-executable',   # Executáveis genéricos
                'application/x-sharedlib',    # Bibliotecas compartilhadas
                'application/x-shellscript',  # Scripts de shell
                'application/x-python',       # Scripts Python
                'application/javascript',     # JavaScript
                'application/x-javascript',   # JavaScript
                'text/javascript',            # JavaScript
                'application/x-httpd-php',    # PHP
                'application/x-php',          # PHP
                'text/x-php',                 # PHP
            ]
            
            # Verificar se é um tipo perigoso
            if any(dm in real_mime for dm in dangerous_mimes):
                os.unlink(temp_file_path)  # Remover arquivo temporário
                return Response({
                    "message": "Arquivo potencialmente perigoso detectado",
                    "detected_type": real_mime,
                    "filename": file.name
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar se a extensão corresponde ao tipo MIME real
            expected_extensions = {
                'image/jpeg': ['jpg', 'jpeg'],
                'image/png': ['png'],
                'application/pdf': ['pdf'],
                'text/plain': ['txt'],
                # Adicione mais mapeamentos conforme necessário
            }
            
            if real_mime in expected_extensions:
                if ext not in expected_extensions[real_mime]:
                    os.unlink(temp_file_path)
                    return Response({
                        "message": "Extensão do arquivo não corresponde ao tipo real",
                        "detected_type": real_mime,
                        "filename": file.name
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Se passou em todas as verificações, processar o arquivo
            file.seek(0)  # Voltar ao início do arquivo para leitura
            
            # Salvar o arquivo
            uploaded_file = UploadedFile(user=request.user, file=file)
            
            try:
                uploaded_file = UploadedFile(user=request.user, file=file)
                uploaded_file.save()
                
                # Se for DICOM, criar registro no Exam
                if file.name.lower().endswith('.dcm') or file.name.lower().endswith('.dicom'):
                    exam = Exam(
                        user=request.user,
                        patient=Patient.objects.first(),  # Exemplo, implementar lógica real
                        status='uploaded'
                    )
                    exam.save()
                    exam.save_original_dicom(uploaded_file.get_file_content())
                    
                    Log.create_log(request.user, f'UPLOAD_DICOM:{file.name}')
                    return Response({
                        "message": "Arquivo DICOM enviado e criptografado com sucesso",
                        "exam_id": exam.id
                    }, status=status.HTTP_201_CREATED)
                if not uploaded_file.exists():
                    raise Exception("O arquivo não foi salvo corretamente")
            except ValidationError as e:
                os.unlink(temp_file_path)
                return Response({"message": f"Erro ao salvar arquivo: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                os.unlink(temp_file_path)
                return Response({"message": f"Erro ao salvar arquivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Remover arquivo temporário após sucesso
            os.unlink(temp_file_path)
            
            Log.create_log(request.user, f'UPLOAD:{file.name}')
            return Response({
                "message": "Arquivo enviado com sucesso",
                "filename": file.name,
                "path": uploaded_file.file.path,
                "mime_type": real_mime  # Retornar o tipo MIME detectado
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "message": f"Erro na verificação de segurança: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FileListView(generics.ListAPIView):
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Listar arquivos enviados",
        operation_description="Lista todos os arquivos enviados pelo usuário. Administradores veem todos os arquivos.",
        responses={200: FileListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        queryset = UploadedFile.objects.all()
        
        # Filtrar apenas arquivos que existem fisicamente
        queryset = [obj for obj in queryset if obj.exists()]
        
        if user.role != 'admin':
            queryset = [obj for obj in queryset if obj.user == user]
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        Log.create_log(request.user, 'LISTAR_ARQUIVOS')
        return response
    
class PatientListView(generics.ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Patient.objects.all()

    @swagger_auto_schema(
        operation_summary="Listar pacientes",
        operation_description="Lista todos os pacientes cadastrados. Acesso para administradores e profissionais de saúde.",
        responses={200: PatientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar novo paciente",
        operation_description="Cria um novo registro de paciente. Acesso para administradores e profissionais de saúde.",
        request_body=PatientSerializer,
        responses={201: PatientSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Patient.objects.all()

    @swagger_auto_schema(
        operation_summary="Detalhes do paciente",
        operation_description="Obtém detalhes de um paciente específico pelo ID.",
        responses={200: PatientSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar paciente",
        operation_description="Atualiza as informações de um paciente existente.",
        request_body=PatientSerializer,
        responses={200: PatientSerializer}
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

class ExamListView(generics.ListCreateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    parser_classes = [MultiPartParser]  # Aceita upload de arquivos
    
    def get_required_roles(self):
        if self.request.method == 'POST':
            return ['health_professional']
        return ['admin', 'health_professional', 'researcher']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Exam.objects.all()
        
        if user.role == 'researcher':
            queryset = queryset.filter(status='segmented')
        elif user.role == 'health_professional':
            queryset = queryset.filter(user=user)
        
        return queryset

    @swagger_auto_schema(
        operation_summary="Listar exames",
        operation_description=(
            "Lista exames de acordo com o perfil do usuário:\n"
            "- Administradores: Todos os exames\n"
            "- Profissionais de saúde: Apenas seus próprios exames\n"
            "- Pesquisadores: Apenas exames anonimizados (segmented)"
        ),
        responses={200: ExamSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar novo exame",
        operation_description="Cria um novo exame com upload de arquivo DICOM",
        request_body=ExamSerializer,
        responses={201: ExamSerializer}
    )
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
            
            if real_mime not in ['application/dicom', 'application/octet-stream']:
                raise ValidationError("Tipo de arquivo inválido. Apenas DICOM é permitido")
            
            # Criar o exame
            exam = Exam(
                patient=serializer.validated_data['patient'],
                user=request.user,
                status='uploaded'
            )
            
            if 'medical_notes' in serializer.validated_data:
                exam.medical_notes = serializer.validated_data['medical_notes']
            
            exam.save()
            
            # Salvar o arquivo DICOM
            filename = f"exam_{exam.id}_{dicom_file.name}"
            exam.original_dicom.save(filename, dicom_file)
            exam.save()
            
            Log.create_log(request.user, f'UPLOAD_DICOM:{filename}')
            headers = self.get_success_headers(serializer.data)
            return Response(ExamSerializer(exam).data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            return Response({"message": f"Erro no processamento: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if temp_file:
                os.unlink(temp_file_path)

class ExamDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    
    def get_required_roles(self):
        exam = self.get_object()
        
        # Apenas o criador do exame ou admin pode editar/excluir
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.role == 'admin':
                return True
            return exam.user == self.request.user
        
        # Visualização permitida para pesquisadores (apenas leitura)
        return ['admin', 'health_professional', 'researcher']
    
    def get_queryset(self):
        return Exam.objects.all()

    @swagger_auto_schema(
        operation_summary="Detalhes do exame",
        operation_description=(
            "Obtém detalhes de um exame específico pelo ID.\n"
            "Permissões:\n"
            "- Administradores: Acesso completo\n"
            "- Profissional de saúde: Apenas seus próprios exames\n"
            "- Pesquisadores: Apenas exames anonimizados"
        ),
        responses={200: ExamSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar exame",
        operation_description=(
            "Atualiza as informações de um exame existente.\n"
            "Permissões:\n"
            "- Apenas administradores ou o profissional de saúde que criou o exame"
        ),
        request_body=ExamSerializer,
        responses={200: ExamSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir exame",
        operation_description=(
            "Exclui permanentemente um registro de exame.\n"
            "Permissões:\n"
            "- Apenas administradores ou o profissional de saúde que criou o exame"
        ),
        responses={204: "Exame excluído com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)