"""Ticket and Comment model CRUD, FK on_delete, and CheckConstraint tests."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from tickets.models import Comment, Ticket, TicketPriority, TicketStatus


User = get_user_model()


@pytest.fixture
def users(db):
    creator = User.objects.create_user(
        email="creator@example.com",
        password="unused",
        name="Creator",
    )
    assignee = User.objects.create_user(
        email="assignee@example.com",
        password="unused",
        name="Assignee",
    )
    return {"creator": creator, "assignee": assignee}


def _make_ticket(creator, **overrides):
    defaults = {
        "title": "Sample ticket",
        "description": "Details here",
        "priority": TicketPriority.MEDIUM,
        "created_by": creator,
    }
    defaults.update(overrides)
    return Ticket.objects.create(**defaults)


# --- Create / Read ---


@pytest.mark.django_db
def test_ticket_defaults_to_open_and_orders_newest_first(users):
    older = _make_ticket(
        users["creator"],
        title="Older",
        description="First ticket",
        priority=TicketPriority.LOW,
    )
    newer = _make_ticket(
        users["creator"],
        title="Newer",
        description="Second ticket",
        priority=TicketPriority.HIGH,
    )

    assert older.status == TicketStatus.OPEN
    assert list(Ticket.objects.values_list("title", flat=True)) == ["Newer", "Older"]


@pytest.mark.django_db
def test_create_ticket_with_all_fields_and_read_back(users):
    ticket = _make_ticket(
        users["creator"],
        title="VPN drops hourly",
        description="Remote staff lose VPN after about 60 minutes.",
        priority=TicketPriority.HIGH,
        assigned_to=users["assignee"],
        status=TicketStatus.IN_PROGRESS,
    )

    loaded = Ticket.objects.select_related("created_by", "assigned_to").get(pk=ticket.pk)

    assert loaded.title == "VPN drops hourly"
    assert loaded.description.startswith("Remote staff")
    assert loaded.priority == TicketPriority.HIGH
    assert loaded.status == TicketStatus.IN_PROGRESS
    assert loaded.created_by_id == users["creator"].id
    assert loaded.assigned_to_id == users["assignee"].id
    assert loaded.created_at is not None
    assert loaded.updated_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize("priority", list(TicketPriority.values))
def test_create_ticket_accepts_each_priority(users, priority):
    ticket = _make_ticket(users["creator"], priority=priority)
    ticket.refresh_from_db()
    assert ticket.priority == priority


@pytest.mark.django_db
@pytest.mark.parametrize("status", list(TicketStatus.values))
def test_create_ticket_accepts_each_status(users, status):
    ticket = _make_ticket(users["creator"], status=status)
    ticket.refresh_from_db()
    assert ticket.status == status


@pytest.mark.django_db
def test_create_ticket_allows_null_assignee(users):
    ticket = _make_ticket(users["creator"], assigned_to=None)
    assert ticket.assigned_to is None


# --- Update ---


@pytest.mark.django_db
def test_update_ticket_fields_persist(users):
    ticket = _make_ticket(users["creator"])
    before = ticket.updated_at

    ticket.title = "Updated title"
    ticket.description = "Updated description"
    ticket.priority = TicketPriority.LOW
    ticket.assigned_to = users["assignee"]
    ticket.save()
    ticket.refresh_from_db()

    assert ticket.title == "Updated title"
    assert ticket.description == "Updated description"
    assert ticket.priority == TicketPriority.LOW
    assert ticket.assigned_to_id == users["assignee"].id
    assert ticket.updated_at >= before


@pytest.mark.django_db
def test_clear_assignee_on_update(users):
    ticket = _make_ticket(users["creator"], assigned_to=users["assignee"])
    ticket.assigned_to = None
    ticket.save(update_fields=["assigned_to", "updated_at"])
    ticket.refresh_from_db()
    assert ticket.assigned_to is None


# --- Comment CRUD ---


@pytest.mark.django_db
def test_comment_create_and_read_on_ticket(users):
    ticket = _make_ticket(users["creator"])
    comment = Comment.objects.create(
        ticket=ticket,
        message="First note",
        created_by=users["creator"],
    )

    assert ticket.comments.count() == 1
    loaded = Comment.objects.get(pk=comment.pk)
    assert loaded.message == "First note"
    assert loaded.ticket_id == ticket.id
    assert loaded.created_by_id == users["creator"].id
    assert loaded.created_at is not None


@pytest.mark.django_db
def test_comment_allowed_on_terminal_ticket(users):
    ticket = _make_ticket(
        users["creator"],
        title="Closed case",
        description="Already closed",
        status=TicketStatus.CLOSED,
    )
    comment = Comment.objects.create(
        ticket=ticket,
        message="Post-close note",
        created_by=users["creator"],
    )

    assert ticket.comments.count() == 1
    assert comment.ticket_id == ticket.id


@pytest.mark.django_db
def test_comments_order_newest_first(users):
    ticket = _make_ticket(users["creator"])
    Comment.objects.create(
        ticket=ticket,
        message="Older comment",
        created_by=users["creator"],
    )
    Comment.objects.create(
        ticket=ticket,
        message="Newer comment",
        created_by=users["assignee"],
    )

    assert list(ticket.comments.values_list("message", flat=True)) == [
        "Newer comment",
        "Older comment",
    ]


@pytest.mark.django_db
def test_duplicate_comments_are_allowed(users):
    ticket = _make_ticket(users["creator"])
    Comment.objects.create(
        ticket=ticket,
        message="Same text",
        created_by=users["creator"],
    )
    Comment.objects.create(
        ticket=ticket,
        message="Same text",
        created_by=users["creator"],
    )
    assert ticket.comments.count() == 2


# --- FK on_delete semantics (data-model.md §1) ---


@pytest.mark.django_db
def test_deleting_assignee_sets_assigned_to_null(users):
    ticket = _make_ticket(users["creator"], assigned_to=users["assignee"])
    users["assignee"].delete()
    ticket.refresh_from_db()
    assert ticket.assigned_to is None
    assert Ticket.objects.filter(pk=ticket.pk).exists()


@pytest.mark.django_db
def test_deleting_creator_is_protected(users):
    ticket = _make_ticket(users["creator"])
    with pytest.raises(ProtectedError):
        users["creator"].delete()
    assert Ticket.objects.filter(pk=ticket.pk).exists()


@pytest.mark.django_db
def test_deleting_comment_author_is_protected(users):
    ticket = _make_ticket(users["creator"])
    Comment.objects.create(
        ticket=ticket,
        message="Protect me",
        created_by=users["assignee"],
    )
    with pytest.raises(ProtectedError):
        users["assignee"].delete()
    assert Comment.objects.filter(message="Protect me").exists()


@pytest.mark.django_db
def test_deleting_ticket_cascades_comments(users):
    ticket = _make_ticket(users["creator"])
    Comment.objects.create(
        ticket=ticket,
        message="Will cascade",
        created_by=users["creator"],
    )
    ticket_id = ticket.id
    ticket.delete()

    assert not Ticket.objects.filter(pk=ticket_id).exists()
    assert not Comment.objects.filter(ticket_id=ticket_id).exists()


# --- CheckConstraints ---


@pytest.mark.django_db
def test_invalid_status_rejected_by_check_constraint(users):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Ticket.objects.create(
                title="Bad status",
                description="Should fail",
                priority=TicketPriority.LOW,
                status="NOT_A_STATUS",
                created_by=users["creator"],
            )
    assert Ticket.objects.count() == 0


@pytest.mark.django_db
def test_invalid_priority_rejected_by_check_constraint(users):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Ticket.objects.create(
                title="Bad priority",
                description="Should fail",
                priority="URGENT",
                created_by=users["creator"],
            )
    assert Ticket.objects.count() == 0
