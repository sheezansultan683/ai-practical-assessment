from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "email", "role")
        read_only_fields = fields


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"


class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token.")
    refresh = serializers.CharField(help_text="JWT refresh token.")


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token.")


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="JWT refresh token.")
