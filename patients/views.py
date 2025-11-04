from rest_framework import generics, permissions
from .models import Paciente
from .serializers import PacienteSerializer
from core.permissions import RoleRequired
from audit.models import Registro
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser

class PacienteListView(generics.ListCreateAPIView):
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Paciente.objects.all()
    parser_classes = [MultiPartParser, FormParser]

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
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('birth_date', openapi.IN_FORM, type=openapi.TYPE_STRING, format='date', required=True),
            openapi.Parameter('medical_info', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        responses={201: PacienteSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PacienteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated, RoleRequired]
    required_roles = ['admin', 'health_professional']
    queryset = Paciente.objects.all()
    parser_classes = [MultiPartParser, FormParser]

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
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('birth_date', openapi.IN_FORM, type=openapi.TYPE_STRING, format='date', required=False),
            openapi.Parameter('medical_info', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
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