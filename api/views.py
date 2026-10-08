from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from . import encryption
from .audit import log_event
from .models import AuditLog, User
from .permissions import IsAdminOrUserRole, IsAdminRole
from .serializers import (
    AdminUserCreateSerializer,
    AuditLogSerializer,
    AvatarSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    RevealSerializer,
    UserSerializer,
    VisibleUserSerializer,
)
from .upload import sanitize_image


class RegisterView(APIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if User.objects.filter(username_index=encryption.blind_index(data['username'])).exists():
            return Response({'msg': 'Username ja existe.'}, status=status.HTTP_400_BAD_REQUEST)

        if data.get('email'):
            if User.objects.filter(email_index=encryption.blind_index(data['email'])).exists():
                return Response({'msg': 'Email ja cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email') or None,
            role=data.get('role', 'user'),
        )
        log_event('REGISTER', user=user, request=request, status_code=201)
        return Response({'msg': 'Usuario criado com sucesso.'}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)
        if user is None:
            log_event(
                'LOGIN_FAILED', request=request, status_code=401,
                detail='credenciais invalidas', subject_plain=username,
            )
            return Response({'msg': 'Credenciais invalidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            log_event(
                'LOGIN_FAILED', user=user, request=request, status_code=403,
                detail='conta inativa', subject_plain=username,
            )
            return Response({'msg': 'Conta inativa.'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        log_event('LOGIN_SUCCESS', user=user, request=request, status_code=200)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.pk,
                'username': user.get_username(),
                'role': user.role_plain,
            },
        })


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh', '')
        revoked = False
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
                revoked = True
            except Exception:
                revoked = False
        log_event('LOGOUT', user=request.user, request=request, status_code=200,
                  detail='token revogado' if revoked else 'sem refresh token')
        return Response({'msg': 'Logout realizado.'})


class UserAdminListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all().order_by('id')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_event('USER_CREATED', user=self.request.user, request=self.request,
                  status_code=201, detail=f'criou usuario id={user.pk}')


class UserRevealView(APIView):
    serializer_class = RevealSerializer
    permission_classes = [IsAdminRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'reveal'

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'msg': 'Usuario nao encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        log_event(
            'REVEAL_PII', user=request.user, request=request, status_code=200,
            detail=f'revelou dados do usuario id={user.pk}',
            subject_plain=user.get_username(),
        )
        return Response(RevealSerializer(user).data)


class PublicUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return User.objects.filter(role_index=encryption.blind_index('public')).order_by('id')


class VisibleUsersView(generics.ListAPIView):
    permission_classes = [IsAdminOrUserRole]
    serializer_class = VisibleUserSerializer

    def get_queryset(self):
        return User.objects.exclude(role_index=encryption.blind_index('admin')).order_by('id')


class MeView(APIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        logs = AuditLog.objects.all()
        action = self.request.query_params.get('action')
        if action:
            logs = logs.filter(action=action)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            logs = logs.filter(user_id=user_id)
        return logs


class UploadAvatarView(APIView):
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'upload'
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get('avatar')
        if uploaded is None:
            return Response({'msg': 'Envie o arquivo no campo avatar.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            name = sanitize_image(uploaded)
        except Exception as exc:
            return Response({'msg': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.avatar = name
        request.user.save(update_fields=['avatar'])
        log_event('UPLOAD', user=request.user, request=request, status_code=201,
                  detail='avatar atualizado')
        return Response({'avatar': request.user.avatar}, status=status.HTTP_201_CREATED)
