# security_api/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

class SwaggerRedirectView(TemplateView):
    template_name = 'swagger_redirect.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['token'] = self.request.GET.get('token', '')
        return context

schema_view = get_schema_view(
   openapi.Info(
      title="Admin API",
      default_version='v1',
      description="""
      <h2>API para Gerenciamento de Segurança</h2>
      <p>Esta API fornece um sistema completo para:</p>
      <ul>
        <li><b>Autenticação de usuários</b> com tokens JWT</li>
        <li><b>Gerenciamento de usuários</b> e administradores</li>
        <li><b>Recuperação segura de senhas</b> via email</li>
        <li><b>Upload e gestão de arquivos</b> com controle de acesso</li>
        <li><b>Registro de auditoria</b> de todas as ações do sistema</li>
      </ul>
      
      <h3>Fluxo de Autenticação</h3>
      <ol>
        <li>Faça login em <code>/api/login/</code> para obter tokens de acesso</li>
        <li>Use o token no formato: <code>Authorization: Bearer &lt;token&gt;</code></li>
        <li>Tokens de acesso expiram em 1 hora - use o refresh token para renovar</li>
      </ol>
      
      <h3>Tipos de Usuários</h3>
      <ul>
        <li><b>Admin:</b> Acesso completo a todos os recursos</li>
        <li><b>User:</b> Acesso limitado aos próprios recursos</li>
      </ul>
      """,
    #   terms_of_service="https://www.example.com/terms/",
    #   contact=openapi.Contact(email="suporte@example.com"),
    #   license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger/redirect/', SwaggerRedirectView.as_view(), name='swagger-redirect'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)