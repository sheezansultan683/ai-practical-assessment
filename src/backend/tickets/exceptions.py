"""Domain exceptions for the ticket lifecycle service layer."""


class TicketServiceError(Exception):
    """Base class for ticket service failures."""

    code: str = "ticket_service_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidTransitionError(TicketServiceError):
    """Known status values, but the edge is not in the allow-list (HTTP 409)."""

    code = "invalid_transition"

    def __init__(
        self,
        *,
        current_status: str,
        attempted_status: str,
        allowed_transitions: list[str],
    ):
        message = (
            f"Cannot transition ticket from {current_status} "
            f"to {attempted_status}."
        )
        details = {
            "current_status": current_status,
            "attempted_status": attempted_status,
            "allowed_transitions": allowed_transitions,
        }
        super().__init__(message, details=details)
        self.current_status = current_status
        self.attempted_status = attempted_status
        self.allowed_transitions = allowed_transitions


class MalformedStatusError(TicketServiceError):
    """Status string is not a valid TicketStatus enum value (HTTP 400)."""

    code = "validation_error"

    def __init__(self, attempted_status: str):
        valid = ", ".join(sorted(self._valid_statuses()))
        message = "Request validation failed."
        details = {
            "status": [
                f'"{attempted_status}" is not a valid choice. '
                f"Valid choices: {valid}."
            ],
        }
        super().__init__(message, details=details)
        self.attempted_status = attempted_status

    @staticmethod
    def _valid_statuses() -> list[str]:
        from tickets.models import TicketStatus

        return list(TicketStatus.values)


class TerminalTicketFrozenError(TicketServiceError):
    """Field updates are not allowed on CLOSED / CANCELLED tickets (HTTP 409)."""

    code = "terminal_ticket_frozen"

    def __init__(self, status: str):
        message = f"Fields on a {status} ticket cannot be updated."
        details = {"status": [status]}
        super().__init__(message, details=details)
        self.status = status


class StatusUpdateNotAllowedError(TicketServiceError):
    """Status must not be changed via the field-update path (HTTP 400)."""

    code = "validation_error"

    def __init__(self):
        message = (
            "Status cannot be changed via this endpoint. "
            "Use POST /api/tickets/{id}/transition/."
        )
        details = {
            "status": [
                "Use POST /api/tickets/{id}/transition/ to change status."
            ],
        }
        super().__init__(message, details=details)
