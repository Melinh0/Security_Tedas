from django.contrib import admin
from .models import Registro

class RegistroAdmin(admin.ModelAdmin):
    list_display = ['profissional', 'action', 'timestamp', 'success']
    list_filter = ['action', 'success', 'timestamp']
    readonly_fields = ['timestamp']

admin.site.register(Registro, RegistroAdmin)