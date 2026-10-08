from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'decrypted_username', 'decrypted_role', 'decrypted_email',
                    'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    ordering = ('id',)
    actions = ['deactivate_users', 'activate_users']
    readonly_fields = (
        'decrypted_username', 'decrypted_email', 'decrypted_role',
        'username_index', 'email_index', 'role_index',
        'date_joined', 'last_login', 'avatar',
    )
    fields = (
        'decrypted_username', 'decrypted_email', 'decrypted_role',
        'is_active', 'is_staff', 'is_superuser',
        'date_joined', 'last_login',
    )

    @admin.display(description='username')
    def decrypted_username(self, obj):
        return obj.get_username()

    @admin.display(description='email')
    def decrypted_email(self, obj):
        return obj.email_plain or '-'

    @admin.display(description='role')
    def decrypted_role(self, obj):
        return obj.role_plain

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if request.method in ('GET', 'HEAD'):
            return True
        return False

    @admin.action(description='Desativar usuarios selecionados')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuario(s) desativado(s).')

    @admin.action(description='Ativar usuarios selecionados')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuario(s) ativado(s).')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'action_display', 'user_display', 'method',
                    'path', 'ip', 'status_code', 'detail')
    list_filter = ('action', 'status_code')
    ordering = ('-timestamp',)
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    @admin.display(description='acao')
    def action_display(self, obj):
        return obj.get_action_display()

    @admin.display(description='usuario')
    def user_display(self, obj):
        if not obj.user:
            return '-'
        return format_html('<a href="/admin/api/user/{}/change/">{}</a>',
                           obj.user.pk, obj.user.get_username())

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
