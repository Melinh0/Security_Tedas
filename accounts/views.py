from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.utils import timezone
from audit.models import Registro
from .models import USER_ROLE_CHOICES, PROFESSIONAL_TYPE_CHOICES
from .serializers import (
    CustomTokenObtainPairSerializer, 
    ProfissionalSaudeSerializer, 
    PasswordResetSerializer,
    AdminCreationSerializer
)
from .permissions import RoleRequired
from django.shortcuts import get_object_or_404
import hashlib
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

ProfissionalSaude = get_user_model()

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login de usuário",
        manual_parameters=[
            openapi.Parameter(
                'username', openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                required=True,
                description="Nome de usuário"
            ),
            openapi.Parameter(
                'password', openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                format='password',
                required=True,
                description="Senha do usuário"
            ),
        ],
        responses={
            200: openapi.Response(description="Login bem-sucedido"),
            401: openapi.Response(description="Credenciais inválidas")
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = ProfissionalSaude.objects.get(username=request.data['username'])
            Registro.criar_registro(user, 'LOGIN', request)
        return response

class ForgotPasswordView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Solicita redefinição de senha",
        manual_parameters=[
            openapi.Parameter(
                'email', openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                format='email',
                required=True,
                description="Email do usuário para redefinição de senha"
            ),
        ],
        responses={
            200: openapi.Response(
                description="Solicitação processada",
                examples={
                    "application/json": {
                        "message": "Se o email estiver cadastrado, enviaremos um link de recuperação",
                        "reset_token": "token_para_desenvolvimento"
                    }
                }
            ),
            500: openapi.Response(description="Erro no servidor de email")
        }
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Verifica se o email existe sem gerar erro 400
        try:
            user = ProfissionalSaude.objects.get(email=email)
            token = user.generate_reset_token()
            
            # Em ambiente de desenvolvimento, vamos apenas retornar o token
            # Em produção, você enviaria por email
            if user.send_reset_email():
                Registro.criar_registro(user, 'SOLICITACAO_RESET_SENHA', request, success=True)
                return Response({
                    "message": "Se o email estiver cadastrado, enviaremos um link de recuperação",
                    "reset_token": token  # Apenas para desenvolvimento
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Erro no servidor de email",
                    "reset_token": token  # Apenas para desenvolvimento
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ProfissionalSaude.DoesNotExist:
            # Não revelamos se o email existe ou não por questões de segurança
            Registro.criar_registro(None, 'SOLICITACAO_RESET_SENHA_INVALIDO', request, success=False)
            return Response({
                "message": "Se o email estiver cadastrado, enviaremos um link de recuperação"
            }, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Redefine a senha usando o token recebido",
        manual_parameters=[
            openapi.Parameter(
                'email', openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                format='email',
                required=True,
                description="Email do usuário"
            ),
            openapi.Parameter(
                'reset_token', openapi.IN_FORM, 
                type=openapi.TYPE_STRING,
                required=True,
                description="Token de redefinição recebido por email"
            ),
            openapi.Parameter(
                'new_password', openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                format='password',
                required=True,
                description="Nova senha"
            ),
        ],
        responses={
            200: openapi.Response(description="Senha redefinida com sucesso"),
            400: openapi.Response(description="Token inválido ou expirado")
        }
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()
        
        try:
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
            
        except ProfissionalSaude.DoesNotExist:
            return Response({"message": "Token inválido ou expirado"}, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListCreateAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Lista todos os profissionais de saúde",
        responses={200: ProfissionalSaudeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Cria um novo profissional de saúde",
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, format='email', required=True),
            openapi.Parameter('cpf', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, format='password', required=True),
            openapi.Parameter('role', openapi.IN_FORM, type=openapi.TYPE_STRING, 
                            enum=[r[0] for r in USER_ROLE_CHOICES], required=True),
            openapi.Parameter('professional_type', openapi.IN_FORM, type=openapi.TYPE_STRING, 
                            enum=[p[0] for p in PROFESSIONAL_TYPE_CHOICES], required=False),
        ],
        responses={201: ProfissionalSaudeSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
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

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return ProfissionalSaude.objects.all()
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
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
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, format='email', required=False),
            openapi.Parameter('cpf', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, format='password', required=False),
            openapi.Parameter('role', openapi.IN_FORM, type=openapi.TYPE_STRING, 
                            enum=[r[0] for r in USER_ROLE_CHOICES], required=False),
            openapi.Parameter('professional_type', openapi.IN_FORM, type=openapi.TYPE_STRING, 
                            enum=[p[0] for p in PROFESSIONAL_TYPE_CHOICES], required=False),
        ],
        responses={200: ProfissionalSaudeSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Excluir usuário",
        operation_description="Exclui um usuário do sistema. Não é possível excluir usuários padrão (admin) ou a si mesmo.",
        responses={204: "Usuário excluído com sucesso"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
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
        
        user_id = user.id
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            Registro.criar_registro(request.user, f'DELETE_USER:{user_id}', request, success=True)
        return response

class AdminListView(generics.ListCreateAPIView):
    serializer_class = AdminCreationSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return ProfissionalSaude.objects.filter(role='admin')
    
    @swagger_auto_schema(
        operation_summary="Listar administradores",
        operation_description="Lista todos os administradores cadastrados no sistema. Apenas administradores podem acessar.",
        responses={200: ProfissionalSaudeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ProfissionalSaudeSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Criar novo administrador",
        operation_description="Cria um novo usuário com perfil de administrador. Apenas administradores podem executar esta ação.",
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, format='email', required=True),
            openapi.Parameter('cpf', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, format='password', required=True),
        ],
        responses={201: ProfissionalSaudeSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        Registro.criar_registro(request.user, f'CRIAR_ADMIN:{user.id}', request, success=True)
        
        response_serializer = ProfissionalSaudeSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfissionalSaudeSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    parser_classes = [MultiPartParser, FormParser]
    
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
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, format='email', required=False),
            openapi.Parameter('cpf', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, format='password', required=False),
        ],
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