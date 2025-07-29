from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'cpf', 'full_name', 'role', 'professional_type')
        
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