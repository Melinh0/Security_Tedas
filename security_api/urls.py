from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
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
        <li><b>Autenticação de usuários</b> com Basic Authentication e tokens JWT</li>
        <li><b>Gerenciamento de usuários</b> com três níveis de acesso (Administrador, Profissional de Saúde, Pesquisador)</li>
        <li><b>Recuperação segura de senhas</b> via email</li>
        <li><b>Upload e gestão de exames DICOM</b> com controle de acesso e criptografia</li>
        <li><b>Registro de auditoria</b> de todas as ações do sistema</li>
        <li><b>Gerenciamento de pacientes</b> com informações médicas criptografadas</li>
      </ul>
      
      <h3>Fluxo de Autenticação Simplificado</h3>
      <ol>
        <li><b>Clique no botão "Authorize" no topo desta página</b></li>
        <li><b>Insira suas credenciais:</b>
          <ul>
            <li>Username: seu nome de usuário (ex: admin)</li>
            <li>Password: sua senha (ex: admin)</li>
          </ul>
        </li>
        <li><b>Pronto!</b> Todas as requisições serão autenticadas automaticamente</li>
      </ol>
      
      <h3>Métodos de Autenticação Disponíveis</h3>
      <ul>
        <li><b>Basic Authentication:</b> Use usuário e senha diretamente (recomendado para testes)</li>
        <li><b>JWT Token:</b> Use tokens JWT obtidos via <code>/api/auth/login/</code></li>
      </ul>

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
        <li><b>/api/auth/login/</b> - Autenticação de usuários (JWT)</li>
        <li><b>/api/auth/forgot-password/</b> - Solicitar recuperação de senha</li>
        <li><b>/api/auth/reset-password/</b> - Redefinir senha com token</li>
        <li><b>/api/profissionais/</b> - Gerenciamento de profissionais de saúde</li>
        <li><b>/api/admins/</b> - Gerenciamento de administradores</li>
        <li><b>/api/pacientes/</b> - Gerenciamento de pacientes</li>
        <li><b>/api/fatias-tomografia/</b> - Upload e gestão de exames de tomografia</li>
        <li><b>/api/registros/</b> - Visualização de registros de auditoria (apenas administradores)</li>
      </ul>

      <h3>Credenciais de Teste (Desenvolvimento)</h3>
      <ul>
        <li><b>Administrador:</b> username: <code>admin</code>, password: <code>admin</code></li>
        <li><b>Pesquisador:</b> username: <code>researcher</code>, password: <code>researcher</code></li>
        <li><b>Médico:</b> username: <code>doctor</code>, password: <code>doctor</code></li>
      </ul>
      """,
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
   authentication_classes=[BasicAuthentication, SessionAuthentication],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('patients.urls')),
    path('api/', include('exams.urls')),
    path('api/', include('audit.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)