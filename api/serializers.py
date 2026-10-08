from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import AuditLog, User

ROLE_CHOICES = ['user', 'public']
USERNAME_VALIDATOR = RegexValidator(
    regex=r'^[\w.@+\- ]+$',
    message='Username contem caracteres invalidos.',
)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=64, min_length=3, validators=[USERNAME_VALIDATOR]
    )
    password = serializers.CharField(max_length=128, write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=False, default='user')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_username(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Username muito curto.')
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128, write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class UserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'date_joined']
        read_only_fields = fields

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_email(self, obj) -> str | None:
        return obj.email_plain

    def get_role(self, obj) -> str:
        return obj.role_plain


class AdminUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=64, min_length=3, validators=[USERNAME_VALIDATOR]
    )
    password = serializers.CharField(max_length=128, write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    role = serializers.ChoiceField(choices=['admin', 'user', 'public'])

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'role']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RevealSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'is_staff', 'date_joined']

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_email(self, obj) -> str | None:
        return obj.email_plain

    def get_role(self, obj) -> str:
        return obj.role_plain


class PublicUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username']

    def get_username(self, obj) -> str:
        return obj.get_username()


class VisibleUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'role']

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_role(self, obj) -> str:
        return obj.role_plain


class MeSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar', 'date_joined']

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_role(self, obj) -> str:
        return obj.role_plain

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            instance.set_email(validated_data['email'])
            validated_data.pop('email')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'username', 'action', 'method', 'path',
            'ip', 'status_code', 'detail', 'subject',
        ]

    def get_username(self, obj) -> str | None:
        return obj.user.get_username() if obj.user else None

    def get_subject(self, obj) -> str:
        return obj.subject_plain


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()
