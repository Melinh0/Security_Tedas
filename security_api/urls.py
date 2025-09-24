#security_api/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="Security TEDAS API",
      default_version='v1',
      description="""
      <h2>API para Gerenciamento de Segurança em Imagens de Fatias de Tomografia</h2>
      <p>Esta API fornece um sistema completo para:</p>
      <ul>
        <li><b>Autenticação de usuários</b> com tokens JWT</li>
        <li><b>Gerenciamento de usuários</b> com três níveis de acesso (Administrador, Profissional de Saúde, Pesquisador)</li>
        <li><b>Recuperação segura de senhas</b> via email</li>
        <li><b>Upload e gestão de exames DICOM</b> com controle de acesso e criptografia</li>
        <li><b>Registro de auditoria</b> de todas as ações do sistema</li>
        <li><b>Gerenciamento de pacientes</b> com informações médicas criptografadas</li>
      </ul>
      
      <h3>Fluxo de Autenticação</h3>
      <ol>
        <li>Faça login em <code>/api/login/</code> para obter tokens de acesso</li>
        <li>Use o token no formato: <code>Authorization: Bearer &lt;token&gt;</code></li>
        <li>Tokens de acesso expiram em 1 hora - use o refresh token para renovar</li>
      </ol>
      
      <h3>Tipos de Usuários</h3>
      <ul>
        <li><b>Administrador:</b> Acesso completo a todos os recursos</li>
        <li><b>Profissional de Saúde:</b> Pode gerenciar pacientes e enviar exames</li>
        <li><b>Pesquisador:</b> Acesso apenas a exames segmentados (dados anonimizados)</li>
      </ul>

      <h3>Funcionalidades Principais</h3>
      <ul>
        <li><b>Upload de Exames:</b> Envio de arquivos DICOM com verificação de tipo MIME</li>
        <li><b>Anonimização:</b> Remoção de dados sensíveis dos arquivos DICOM</li>
        <li><b>Segmentação:</b> Processamento de imagens para identificação de regiões de interesse</li>
        <li><b>Criptografia:</b> Dados sensíveis são criptografados no banco de dados e no sistema de arquivos</li>
      </ul>

      <h3>Endpoints Principais</h3>
      <ul>
        <li><b>/api/login/</b> - Autenticação de usuários</li>
        <li><b>/api/profissional-saude/</b> - Gerenciamento de profissionais de saúde</li>
        <li><b>/api/pacientes/</b> - Gerenciamento de pacientes</li>
        <li><b>/api/fatias-tomografia/</b> - Upload e gestão de exames de tomografia</li>
        <li><b>/api/registros/</b> - Visualização de registros de auditoria (apenas administradores)</li>
      </ul>
      """,
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)