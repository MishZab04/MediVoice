from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_approved:
            raise serializers.ValidationError(
                'Your account is pending admin approval. You will be notified once approved.'
            )
        data['user'] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'facility_name',
            'is_active', 'is_approved', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'role']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Used on the /me/ endpoint — role cannot be changed here."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'facility_name']


class CreateHealthWorkerSerializer(serializers.ModelSerializer):
    """Admin-created health workers are approved immediately."""

    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'phone_number', 'facility_name']

    def create(self, validated_data):
        return User.objects.create_user(
            role=UserRole.HEALTH_WORKER,
            is_approved=True,
            **validated_data,
        )


class SignUpSerializer(serializers.ModelSerializer):
    """Self-registration — account starts as pending approval."""

    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'phone_number', 'facility_name']

    def create(self, validated_data):
        return User.objects.create_user(
            role=UserRole.HEALTH_WORKER,
            is_approved=False,
            **validated_data,
        )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text='The refresh token to blacklist.')
