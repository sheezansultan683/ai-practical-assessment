"""Shared OpenAPI components for drf-spectacular (NFR-10)."""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=(
            "Machine-readable code "
            "(validation_error, authentication_failed, not_found, "
            "invalid_transition, terminal_ticket_frozen, …)."
        ),
    )
    message = serializers.CharField(help_text="Human-readable summary.")
    details = serializers.JSONField(
        allow_null=True,
        required=False,
        help_text="Field-level map (field → string[]) when applicable; else null.",
    )


class ErrorEnvelopeSerializer(serializers.Serializer):
    error = ErrorBodySerializer()


ERROR_ENVELOPE_EXAMPLE = OpenApiExample(
    "Error envelope",
    value={
        "error": {
            "code": "validation_error",
            "message": "Request validation failed.",
            "details": {"title": ["This field may not be blank."]},
        }
    },
    response_only=True,
)


def error_response(description: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=ErrorEnvelopeSerializer,
        description=description,
        examples=[ERROR_ENVELOPE_EXAMPLE],
    )


AUTH_401 = error_response(
    "Missing, expired, or invalid JWT access token.",
)
NOT_FOUND_404 = error_response("Resource not found.")
VALIDATION_400 = error_response("Malformed or invalid input.")
CONFLICT_409 = error_response(
    "Lifecycle forbids the operation (invalid transition or terminal ticket).",
)


def paginated_ticket_list_serializer():
    """Lazy import to avoid tickets ↔ config import cycles at module load."""
    from tickets.serializers import TicketListSerializer

    class PaginatedTicketListSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        page = serializers.IntegerField()
        page_size = serializers.IntegerField()
        results = TicketListSerializer(many=True)

    return PaginatedTicketListSerializer
