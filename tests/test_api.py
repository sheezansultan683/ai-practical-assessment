"""API integration tests for auth, tickets, comments, and CSV export."""

import csv
import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tickets.models import Ticket, TicketPriority, TicketStatus


User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def users(db):
    agent = User.objects.create_user(
        email="priya.nair@example.com",
        password="SeedPass!23",
        name="Priya Nair",
        role="AGENT",
    )
    other = User.objects.create_user(
        email="james.okonkwo@example.com",
        password="SeedPass!23",
        name="James Okonkwo",
        role="AGENT",
    )
    return {"agent": agent, "other": other}


def _auth(api, user):
    refresh = RefreshToken.for_user(user)
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return refresh


@pytest.mark.django_db
def test_login_with_email_returns_tokens(api, users):
    response = api.post(
        "/api/token/",
        {"email": "priya.nair@example.com", "password": "SeedPass!23"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_unauthenticated_ticket_list_returns_401_envelope(api):
    response = api.get("/api/tickets/")
    assert response.status_code == 401
    assert response.data["error"]["code"] == "authentication_failed"


@pytest.mark.django_db
def test_me_and_users_list(api, users):
    _auth(api, users["agent"])
    me = api.get("/api/me/")
    assert me.status_code == 200
    assert me.data["email"] == "priya.nair@example.com"
    assert set(me.data.keys()) == {"id", "name", "email", "role"}

    listing = api.get("/api/users/")
    assert listing.status_code == 200
    assert len(listing.data) == 2


@pytest.mark.django_db
def test_create_list_detail_transition_comment_export(api, users):
    _auth(api, users["agent"])

    create = api.post(
        "/api/tickets/",
        {
            "title": "VPN disconnects every hour",
            "description": "Remote staff lose VPN after about 60 minutes.",
            "priority": "HIGH",
            "assigned_to": users["other"].id,
            "created_by": users["other"].id,
            "status": "CLOSED",
        },
        format="json",
    )
    assert create.status_code == 201
    assert create.data["status"] == "OPEN"
    assert create.data["created_by"]["id"] == users["agent"].id
    assert create.data["allowed_transitions"] == ["IN_PROGRESS", "CANCELLED"]
    assert create.data["comments"] == []
    ticket_id = create.data["id"]

    listing = api.get("/api/tickets/")
    assert listing.status_code == 200
    assert listing.data["page"] == 1
    assert listing.data["page_size"] == 20
    assert listing.data["count"] == 1

    filtered = api.get("/api/tickets/?status=OPEN&q=vpn")
    assert filtered.status_code == 200
    assert filtered.data["count"] == 1

    bad_filter = api.get("/api/tickets/?status=NOPE")
    assert bad_filter.status_code == 400
    assert bad_filter.data["error"]["code"] == "validation_error"

    detail = api.get(f"/api/tickets/{ticket_id}/")
    assert detail.status_code == 200
    assert "comments" in detail.data

    bad_transition = api.post(
        f"/api/tickets/{ticket_id}/transition/",
        {"status": "RESOLVED"},
        format="json",
    )
    assert bad_transition.status_code == 409
    assert bad_transition.data["error"]["code"] == "invalid_transition"
    assert Ticket.objects.get(pk=ticket_id).status == TicketStatus.OPEN

    good_transition = api.post(
        f"/api/tickets/{ticket_id}/transition/",
        {"status": "IN_PROGRESS"},
        format="json",
    )
    assert good_transition.status_code == 200
    assert good_transition.data["status"] == "IN_PROGRESS"

    patch_status = api.patch(
        f"/api/tickets/{ticket_id}/",
        {"status": "RESOLVED"},
        format="json",
    )
    assert patch_status.status_code == 400
    assert patch_status.data["error"]["code"] == "validation_error"

    patch_fields = api.patch(
        f"/api/tickets/{ticket_id}/",
        {"title": "VPN drops hourly", "priority": "MEDIUM"},
        format="json",
    )
    assert patch_fields.status_code == 200
    assert patch_fields.data["title"] == "VPN drops hourly"

    comment = api.post(
        f"/api/tickets/{ticket_id}/comments/",
        {"message": "Reproduced on two laptops."},
        format="json",
    )
    assert comment.status_code == 201
    assert comment.data["ticket_id"] == ticket_id
    assert comment.data["created_by"]["id"] == users["agent"].id

    # Other user's tickets must not appear in export.
    other_ticket = Ticket.objects.create(
        title="Other owned",
        description="Should not export",
        priority=TicketPriority.LOW,
        created_by=users["other"],
    )
    export = api.get("/api/tickets/export/")
    assert export.status_code == 200
    assert export["Content-Type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(export.content.decode())))
    assert rows[0][0] == "id"
    assert len(rows) == 2
    assert rows[1][0] == str(ticket_id)
    assert str(other_ticket.id) not in {row[0] for row in rows[1:]}


@pytest.mark.django_db
def test_terminal_freeze_and_comment_allowed(api, users):
    _auth(api, users["agent"])
    ticket = Ticket.objects.create(
        title="Closed case",
        description="Done",
        priority=TicketPriority.LOW,
        status=TicketStatus.CLOSED,
        created_by=users["agent"],
    )

    frozen = api.patch(
        f"/api/tickets/{ticket.id}/",
        {"title": "Nope"},
        format="json",
    )
    assert frozen.status_code == 409
    assert frozen.data["error"]["code"] == "terminal_ticket_frozen"

    comment = api.post(
        f"/api/tickets/{ticket.id}/comments/",
        {"message": "Note after close"},
        format="json",
    )
    assert comment.status_code == 201


@pytest.mark.django_db
def test_export_header_only_when_no_tickets(api, users):
    _auth(api, users["agent"])
    export = api.get("/api/tickets/export/")
    assert export.status_code == 200
    rows = list(csv.reader(io.StringIO(export.content.decode())))
    assert len(rows) == 1


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api, users):
    refresh = _auth(api, users["agent"])
    logout = api.post(
        "/api/token/blacklist/",
        {"refresh": str(refresh)},
        format="json",
    )
    assert logout.status_code in {200, 205}

    reuse = api.post(
        "/api/token/refresh/",
        {"refresh": str(refresh)},
        format="json",
    )
    assert reuse.status_code == 401


def test_openapi_schema_documents_core_endpoints(api):
    """OpenAPI is generated from code (NFR-10), not hand-maintained."""
    response = api.get("/api/schema/", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Support Ticket Management API"
    paths = schema["paths"]
    expected = {
        "/api/token/",
        "/api/token/refresh/",
        "/api/token/blacklist/",
        "/api/me/",
        "/api/users/",
        "/api/tickets/",
        "/api/tickets/{id}/",
        "/api/tickets/{id}/transition/",
        "/api/tickets/{id}/comments/",
        "/api/tickets/export/",
    }
    assert expected.issubset(paths.keys())
    assert "jwtAuth" in schema["components"]["securitySchemes"]

    docs = api.get("/api/docs/")
    assert docs.status_code == 200
