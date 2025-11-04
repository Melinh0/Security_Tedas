from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import FatiaTomografia
from .serializers import FatiaTomografiaSerializer
from core.permissions import RoleRequired
from audit.models import Registro
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import tempfile
import os
import magic
from django.core.exceptions import ValidationError

class FatiaTomografiaListView(generics.ListCreateAPIView):
    serializer_class = FatiaTomografiaSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    parser_classes = [MultiPartParser, FormParser]
    
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

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['profissional'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        dicom_file = serializer.validated_data.get('dicom_file')
        if not dicom_file:
            return Response({"message": "Arquivo DICOM é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        temp_file = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in dicom_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            mime = magic.Magic(mime=True)
            real_mime = mime.from_file(temp_file_path)
            
            if real_mime not in settings.DICOM_ALLOWED_MIME_TYPES:
                raise ValidationError("Tipo de arquivo inválido. Apenas DICOM é permitido")
            
            fatia_tomografia = serializer.save(profissional=request.user)
            
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
    parser_classes = [MultiPartParser, FormParser]
    
    def get_required_roles(self):
        fatia_tomografia = self.get_object()
        
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.role == 'admin':
                return True
            return fatia_tomografia.profissional == self.request.user
        
        return ['admin', 'health_professional', 'researcher']
    
    def get_queryset(self):
        return FatiaTomografia.objects.all()