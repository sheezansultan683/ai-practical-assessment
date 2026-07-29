from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from tickets.exceptions import TicketServiceError


def _envelope(code: str, message: str, details=None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def custom_exception_handler(exc, context):
    if isinstance(exc, TicketServiceError):
        http_status = {
            "invalid_transition": status.HTTP_409_CONFLICT,
            "terminal_ticket_frozen": status.HTTP_409_CONFLICT,
            "validation_error": status.HTTP_400_BAD_REQUEST,
        }.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return Response(
            _envelope(exc.code, exc.message, exc.details),
            status=http_status,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = "validation_error"
    message = "Request validation failed."
    details = None

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "authentication_failed"
        message = "Authentication credentials were not provided or are invalid."
        details = None
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code = "permission_denied"
        message = "You do not have permission to perform this action."
        details = None
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "not_found"
        message = "Not found."
        details = None
    elif isinstance(response.data, dict):
        # DRF validation / auth detail shapes → one envelope.
        if "detail" in response.data and len(response.data) == 1:
            detail = response.data["detail"]
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                code = "authentication_failed"
                message = str(detail)
            else:
                message = str(detail)
            details = None
        else:
            details = {
                key: (
                    [str(item) for item in value]
                    if isinstance(value, (list, tuple))
                    else [str(value)]
                )
                for key, value in response.data.items()
            }
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                code = "authentication_failed"
                message = "Authentication failed."

    response.data = _envelope(code, message, details)
    return response
