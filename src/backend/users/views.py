from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from config.schema import AUTH_401, VALIDATION_400
from .serializers import (
    EmailTokenObtainPairSerializer,
    TokenPairResponseSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="Obtain access and refresh tokens",
    description=(
        "Authenticate a seeded user with email + password. "
        "Returns JWT access and refresh tokens."
    ),
    request=EmailTokenObtainPairSerializer,
    responses={
        200: TokenPairResponseSerializer,
        400: VALIDATION_400,
        401: AUTH_401,
    },
)
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Current user profile",
        description="Return the authenticated user's id, name, email, and role.",
        responses={200: UserSerializer, 401: AUTH_401},
    )
)
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="List seeded users",
        description=(
            "Return seeded users for the assignee picker. "
            "Not paginated (seed set is small). No user CRUD."
        ),
        responses={200: UserSerializer(many=True), 401: AUTH_401},
    )
)
class UserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")
    pagination_class = None
