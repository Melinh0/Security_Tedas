from rest_framework import serializers
from .models import FatiaTomografia
from patients.models import Paciente

class FatiaTomografiaSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='paciente.full_name', read_only=True)
    user_name = serializers.CharField(source='profissional.full_name', read_only=True)
    dicom_url = serializers.SerializerMethodField()
    dicom_file = serializers.FileField(write_only=True, required=False)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(),
        source='paciente',
        write_only=True
    )
    medical_notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FatiaTomografia
        fields = [
            'id', 'paciente_id', 'patient_name', 'profissional', 'user_name', 
            'status', 'uploaded_at', 'updated_at', 'medical_notes',
            'dicom_url', 'dicom_file', 'segmentation_path', 'mask_path'
        ]
        extra_kwargs = {
            'profissional': {'read_only': True},
        }
    
    def get_dicom_url(self, obj):
        if obj.original_dicom:
            return obj.original_dicom.url
        return None