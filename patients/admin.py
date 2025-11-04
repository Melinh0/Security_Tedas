from django.contrib import admin
from .models import Paciente

class PacienteAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_date', 'created_at']
    search_fields = ['full_name']
    list_filter = ['created_at']

admin.site.register(Paciente, PacienteAdmin)