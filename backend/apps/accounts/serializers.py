from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "is_active", "date_joined")
        read_only_fields = ("id", "role", "is_active", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("email", "full_name", "password")

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # A self-registered user must be immediately usable in the portal.
        from apps.customers.models import Customer
        Customer.objects.create(user=user, name=user.full_name, email=user.email)
        return user


class CreateStaffSerializer(RegisterSerializer):
    role = serializers.ChoiceField(choices=[User.Role.STAFF, User.Role.ADMIN], default=User.Role.STAFF)

    class Meta(RegisterSerializer.Meta):
        fields = ("email", "full_name", "password", "role")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": ["Current password is incorrect."]})
        password_validation.validate_password(attrs["new_password"], user)
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].lower().strip()
        return super().validate(attrs)
