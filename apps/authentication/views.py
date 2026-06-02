import logging

from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    CreateHealthWorkerSerializer,
    LogoutSerializer,
    SignUpSerializer,
)
from .permissions import IsAdmin

logger = logging.getLogger('apps.authentication')


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns access token, refresh token, and user profile.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the supplied refresh token, invalidating the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            logger.info('User %s logged out', request.user.email)
            return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {'detail': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/me/  — return the authenticated user's profile
    PATCH /api/v1/auth/me/ — update name, phone, facility (role is read-only here)
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateProfileSerializer
        return UserSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class SignUpView(generics.CreateAPIView):
    """
    POST /api/v1/auth/signup/
    Public registration for health workers. Returns JWT tokens on success.
    """
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info('New health worker registered: %s', user.email)
        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class HealthWorkerViewSet(viewsets.ModelViewSet):
    """
    CRUD for health worker accounts — Admin only.

    GET    /api/v1/auth/users/
    POST   /api/v1/auth/users/
    GET    /api/v1/auth/users/{id}/
    PATCH  /api/v1/auth/users/{id}/
    DELETE /api/v1/auth/users/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.filter(role='health_worker').order_by('-date_joined')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateHealthWorkerSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        # Soft-delete: deactivate instead of hard delete to preserve audit trail
        instance.is_active = False
        instance.save(update_fields=['is_active'])
