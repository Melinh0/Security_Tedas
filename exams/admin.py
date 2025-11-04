from django.contrib import admin
from .models import FatiaTomografia

class FatiaTomografiaAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'profissional', 'status', 'uploaded_at']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['paciente__full_name']

admin.site.register(FatiaTomografia, FatiaTomografiaAdmin)