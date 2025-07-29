# api/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm 
    model = CustomUser
    list_display = ['username', 'email', 'full_name', 'role', 'professional_type', 'is_staff', 'is_active']
    list_filter = ['role', 'professional_type', 'is_staff']  # Adicionado professional_type
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('full_name', 'email', 'cpf', 'professional_type')}),  # Atualizado
        ('Permissões', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Tokens', {'fields': ('reset_token', 'reset_token_exp')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'cpf', 'full_name', 'password1', 'password2', 
                       'role', 'professional_type'),
        }),
    )
    search_fields = ('email', 'username', 'full_name', 'cpf')
    ordering = ('full_name',)

admin.site.register(CustomUser, CustomUserAdmin)