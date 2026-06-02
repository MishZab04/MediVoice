from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed user info in the JWT payload so clients don't need a separate /me call
        token['role'] = user.role
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include the full user profile in the login response body
        data['user'] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'facility_name',
            'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'role']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Used on the /me/ endpoint — role cannot be changed here."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'facility_name']


class CreateHealthWorkerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'phone_number', 'facility_name']

    def create(self, validated_data):
        return User.objects.create_user(
            role=UserRole.HEALTH_WORKER,
            **validated_data,
        )


SignUpSerializer = CreateHealthWorkerSerializer


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text='The refresh token to blacklist.')
