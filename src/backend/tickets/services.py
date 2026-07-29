"""Ticket lifecycle service — single source of truth for status transitions."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from tickets.exceptions import (
    InvalidTransitionError,
    MalformedStatusError,
    StatusUpdateNotAllowedError,
    TerminalTicketFrozenError,
)
from tickets.models import Comment, Ticket, TicketStatus

User = get_user_model()

# Exactly one allow-list definition for the whole codebase (NFR-3).
ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    TicketStatus.OPEN: (TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED),
    TicketStatus.IN_PROGRESS: (TicketStatus.RESOLVED, TicketStatus.CANCELLED),
    TicketStatus.RESOLVED: (TicketStatus.CLOSED,),
    TicketStatus.CLOSED: (),
    TicketStatus.CANCELLED: (),
}

TERMINAL_STATUSES = frozenset(
    {TicketStatus.CLOSED, TicketStatus.CANCELLED},
)

EDITABLE_FIELDS = frozenset(
    {"title", "description", "priority", "assigned_to"},
)


def allowed_transitions(status: str) -> list[str]:
    """Return legal next statuses for the given current status."""
    if status not in TicketStatus.values:
        raise MalformedStatusError(status)
    return list(ALLOWED_TRANSITIONS[status])


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES


@transaction.atomic
def create_ticket(
    *,
    created_by,
    title: str,
    description: str,
    priority: str,
    assigned_to=None,
) -> Ticket:
    """Create a ticket; status is always OPEN; created_by is the actor."""
    return Ticket.objects.create(
        title=title,
        description=description,
        priority=priority,
        status=TicketStatus.OPEN,
        assigned_to=assigned_to,
        created_by=created_by,
    )


@transaction.atomic
def add_comment(*, ticket: Ticket, created_by, message: str) -> Comment:
    """Append a comment on any ticket status (including terminal)."""
    return Comment.objects.create(
        ticket=ticket,
        message=message,
        created_by=created_by,
    )


@transaction.atomic
def transition_ticket(ticket: Ticket, to_status: str) -> Ticket:
    """
    Move ticket to to_status if the edge is allowed.

    Raises MalformedStatusError for unknown enum strings (400 path).
    Raises InvalidTransitionError for allow-list misses (409 path).
    On failure the ticket status in the DB is unchanged.
    """
    if to_status not in TicketStatus.values:
        raise MalformedStatusError(to_status)

    current = ticket.status
    allowed = allowed_transitions(current)
    if to_status not in allowed:
        raise InvalidTransitionError(
            current_status=current,
            attempted_status=to_status,
            allowed_transitions=allowed,
        )

    ticket.status = to_status
    ticket.save(update_fields=["status", "updated_at"])
    return ticket


@transaction.atomic
def update_ticket_fields(ticket: Ticket, **fields: Any) -> Ticket:
    """
    Update editable fields on a non-terminal ticket.

    Rejects status changes (use transition_ticket) and freezes CLOSED/CANCELLED.
    """
    if "status" in fields:
        raise StatusUpdateNotAllowedError()

    if is_terminal(ticket.status):
        raise TerminalTicketFrozenError(ticket.status)

    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(
            f"Unsupported update fields: {', '.join(sorted(unknown))}"
        )

    update_fields: list[str] = []
    for name, value in fields.items():
        setattr(ticket, name, value)
        update_fields.append(name)

    if update_fields:
        update_fields.append("updated_at")
        ticket.save(update_fields=update_fields)

    return ticket
