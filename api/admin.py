# api/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ProfissionalSaude, Paciente, FatiaTomografia, Registro
from .forms import ProfissionalSaudeCreationForm

class ProfissionalSaudeAdmin(UserAdmin):
    add_form = ProfissionalSaudeCreationForm 
    model = ProfissionalSaude
    list_display = ['username', 'email', 'full_name', 'role', 'professional_type', 'is_staff', 'is_active']
    list_filter = ['role', 'professional_type', 'is_staff']
    
    # Campos para edição
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('full_name', 'email', '_cpf', 'professional_type')}),
        ('Permissões', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Tokens', {'fields': ('reset_token', 'reset_token_exp')}),
    )
    
    # Campos para criação
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'password1', 'password2', 
                       'role', 'professional_type'),
        }),
    )
    search_fields = ('email', 'username', 'full_name')
    ordering = ('full_name',)

admin.site.register(ProfissionalSaude, ProfissionalSaudeAdmin)
admin.site.register(Registro)
admin.site.register(Paciente)
admin.site.register(FatiaTomografia)