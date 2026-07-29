"""Full transition-matrix and lifecycle service tests (no HTTP views)."""

import pytest
from django.contrib.auth import get_user_model

from tickets.exceptions import (
    InvalidTransitionError,
    MalformedStatusError,
    StatusUpdateNotAllowedError,
    TerminalTicketFrozenError,
)
from tickets.models import Ticket, TicketPriority, TicketStatus
from tickets.services import (
    ALLOWED_TRANSITIONS,
    allowed_transitions,
    transition_ticket,
    update_ticket_fields,
)


User = get_user_model()

ALL_STATUSES = list(TicketStatus.values)


def _ticket(*, status: str = TicketStatus.OPEN) -> Ticket:
    user = User.objects.create_user(
        email=f"agent-{status.lower()}@example.com",
        password="unused",
        name="Agent",
    )
    return Ticket.objects.create(
        title=f"Ticket in {status}",
        description="Lifecycle test ticket",
        priority=TicketPriority.MEDIUM,
        status=status,
        created_by=user,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (src, dst)
        for src, destinations in ALLOWED_TRANSITIONS.items()
        for dst in destinations
    ],
)
def test_valid_transitions_succeed(from_status, to_status):
    ticket = _ticket(status=from_status)
    before = ticket.updated_at

    result = transition_ticket(ticket, to_status)
    ticket.refresh_from_db()

    assert result.status == to_status
    assert ticket.status == to_status
    assert ticket.updated_at >= before
    assert allowed_transitions(ticket.status) == list(
        ALLOWED_TRANSITIONS[to_status]
    )


@pytest.mark.django_db
@pytest.mark.parametrize("from_status", ALL_STATUSES)
@pytest.mark.parametrize("to_status", ALL_STATUSES)
def test_invalid_transitions_rejected_and_status_unchanged(from_status, to_status):
    if to_status in ALLOWED_TRANSITIONS[from_status]:
        pytest.skip("valid edge covered elsewhere")

    ticket = _ticket(status=from_status)
    original_updated_at = ticket.updated_at

    with pytest.raises(InvalidTransitionError) as exc_info:
        transition_ticket(ticket, to_status)

    ticket.refresh_from_db()
    err = exc_info.value
    assert ticket.status == from_status
    assert ticket.updated_at == original_updated_at
    assert err.code == "invalid_transition"
    assert err.current_status == from_status
    assert err.attempted_status == to_status
    assert err.allowed_transitions == list(ALLOWED_TRANSITIONS[from_status])
    assert err.details["allowed_transitions"] == err.allowed_transitions


@pytest.mark.django_db
def test_unknown_status_string_is_malformed_not_conflict():
    ticket = _ticket(status=TicketStatus.OPEN)

    with pytest.raises(MalformedStatusError) as exc_info:
        transition_ticket(ticket, "in_progress")

    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.OPEN
    assert exc_info.value.code == "validation_error"


@pytest.mark.django_db
def test_allowed_transitions_for_each_status():
    assert allowed_transitions(TicketStatus.OPEN) == [
        TicketStatus.IN_PROGRESS,
        TicketStatus.CANCELLED,
    ]
    assert allowed_transitions(TicketStatus.IN_PROGRESS) == [
        TicketStatus.RESOLVED,
        TicketStatus.CANCELLED,
    ]
    assert allowed_transitions(TicketStatus.RESOLVED) == [TicketStatus.CLOSED]
    assert allowed_transitions(TicketStatus.CLOSED) == []
    assert allowed_transitions(TicketStatus.CANCELLED) == []


@pytest.mark.django_db
def test_status_cannot_be_changed_via_field_update():
    ticket = _ticket(status=TicketStatus.OPEN)

    with pytest.raises(StatusUpdateNotAllowedError) as exc_info:
        update_ticket_fields(ticket, status=TicketStatus.IN_PROGRESS)

    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.OPEN
    assert exc_info.value.code == "validation_error"
    assert "transition" in exc_info.value.message.lower()


@pytest.mark.django_db
@pytest.mark.parametrize("status", [TicketStatus.CLOSED, TicketStatus.CANCELLED])
def test_field_updates_frozen_on_terminal_tickets(status):
    ticket = _ticket(status=status)
    original_title = ticket.title

    with pytest.raises(TerminalTicketFrozenError) as exc_info:
        update_ticket_fields(ticket, title="Should not stick")

    ticket.refresh_from_db()
    assert ticket.title == original_title
    assert ticket.status == status
    assert exc_info.value.code == "terminal_ticket_frozen"


@pytest.mark.django_db
def test_field_updates_allowed_on_non_terminal_ticket():
    ticket = _ticket(status=TicketStatus.IN_PROGRESS)

    update_ticket_fields(
        ticket,
        title="Updated title",
        priority=TicketPriority.HIGH,
        assigned_to=None,
    )
    ticket.refresh_from_db()

    assert ticket.title == "Updated title"
    assert ticket.priority == TicketPriority.HIGH
    assert ticket.status == TicketStatus.IN_PROGRESS
