#api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from .models import Log, UploadedFile
from .serializers import (
    CustomTokenObtainPairSerializer, 
    UserSerializer, 
    PasswordResetSerializer,
    LogSerializer,
    FileUploadSerializer,
    FileListSerializer
)
from .permissions import RoleRequired
from django.shortcuts import get_object_or_404
import os
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(username=request.data['username'])
            Log.create_log(user, 'LOGIN')
        return response

class ForgotPasswordView(APIView):
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
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        user = get_object_or_404(User, email=email, reset_token=reset_token)
        
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
        
        # Prevenções de deleção
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

class AdminListView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = 'admin'
    
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

class FileUploadView(APIView):
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"message": "Nenhum arquivo enviado"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        if not file.name:
            return Response({"message": "Nome de arquivo vazio"}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar extensões permitidas
        if settings.ALLOWED_EXTENSIONS:
            ext = os.path.splitext(file.name)[1].lower().lstrip('.')
            if ext not in settings.ALLOWED_EXTENSIONS:
                return Response({"message": f"Extensão .{ext} não permitida"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Salvar o arquivo
        uploaded_file = UploadedFile(user=request.user, file=file)
        try:
            uploaded_file.full_clean()
            uploaded_file.save()
        except ValidationError as e:
            return Response({"message": f"Erro ao salvar arquivo: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"Erro ao salvar arquivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        Log.create_log(request.user, f'UPLOAD:{file.name}')
        return Response({
            "message": "Arquivo enviado com sucesso",
            "filename": file.name,
            "path": uploaded_file.file.path
        }, status=status.HTTP_201_CREATED)

class FileListView(generics.ListAPIView):
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return UploadedFile.objects.all()
        return UploadedFile.objects.filter(user=user)
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        Log.create_log(request.user, 'LISTAR_ARQUIVOS')
        return response