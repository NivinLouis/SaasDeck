from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.permissions import IsAdmin
from .models import User
from .serializers import ChangePasswordSerializer, CreateStaffSerializer, EmailTokenObtainPairSerializer, LogoutSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """JWT login; access expires in 15 minutes and refresh tokens rotate."""
    serializer_class = EmailTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    pass


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except Exception:
            return Response({"code": "invalid_token", "message": "Refresh token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffCreateView(generics.CreateAPIView):
    serializer_class = CreateStaffSerializer
    permission_classes = [IsAdmin]


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "full_name"]
    ordering_fields = ["email", "full_name", "date_joined"]
    queryset = User.objects.all().order_by("id")
