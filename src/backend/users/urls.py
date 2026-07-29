from django.urls import path
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from config.schema import AUTH_401, VALIDATION_400
from .serializers import (
    AccessTokenResponseSerializer,
    RefreshTokenRequestSerializer,
)
from .views import EmailTokenObtainPairView, MeView, UserListView


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        description=(
            "Exchange a valid refresh token for a new access token "
            "without re-entering credentials."
        ),
        request=RefreshTokenRequestSerializer,
        responses={
            200: AccessTokenResponseSerializer,
            400: VALIDATION_400,
            401: AUTH_401,
        },
    )
)
class DocumentedTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Logout (blacklist refresh token)",
        description=(
            "Invalidate the refresh token so it cannot be reused. "
            "Returns 205 Reset Content on success."
        ),
        request=RefreshTokenRequestSerializer,
        responses={400: VALIDATION_400, 401: AUTH_401},
    )
)
class DocumentedTokenBlacklistView(TokenBlacklistView):
    pass


urlpatterns = [
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "token/refresh/",
        DocumentedTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "token/blacklist/",
        DocumentedTokenBlacklistView.as_view(),
        name="token_blacklist",
    ),
    path("me/", MeView.as_view(), name="me"),
    path("users/", UserListView.as_view(), name="user-list"),
]
