#api/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import ProfissionalSaude

class ProfissionalSaudeCreationForm(UserCreationForm):
    class Meta:
        model = ProfissionalSaude
        fields = ('username', 'email', 'full_name', 'role', 'professional_type')
        
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        professional_type = cleaned_data.get('professional_type')
        
        if role == 'health_professional' and not professional_type:
            raise forms.ValidationError(
                "Tipo profissional é obrigatório para profissionais da saúde"
            )
            
        if role != 'health_professional' and professional_type:
            cleaned_data['professional_type'] = None
            
        return cleaned_data