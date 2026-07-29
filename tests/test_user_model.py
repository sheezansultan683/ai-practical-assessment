"""Custom User model CRUD, identity, and constraint tests."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from users.models import UserRole


User = get_user_model()


# --- Create ---


@pytest.mark.django_db
def test_create_user_uses_email_as_identity():
    user = User.objects.create_user(
        email="agent@example.com",
        name="Support Agent",
    )

    assert user.email == "agent@example.com"
    assert user.role == UserRole.AGENT
    assert not user.has_usable_password()
    assert not hasattr(user, "username")
    assert User.USERNAME_FIELD == "email"


@pytest.mark.django_db
def test_create_user_with_password_and_check():
    user = User.objects.create_user(
        email="priya.nair@example.com",
        password="SeedPass!23",
        name="Priya Nair",
        role=UserRole.AGENT,
    )

    assert user.check_password("SeedPass!23")
    assert not user.check_password("wrong-password")
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.date_joined is not None


@pytest.mark.django_db
def test_create_superuser_sets_admin_flags():
    user = User.objects.create_superuser(
        email="admin@example.com",
        name="Support Admin",
        password="AdminPass!23",
    )

    assert user.role == UserRole.ADMIN
    assert user.is_staff
    assert user.is_superuser
    assert user.check_password("AdminPass!23")


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user(email="", name="No Email")


@pytest.mark.django_db
def test_create_user_normalizes_email():
    user = User.objects.create_user(
        email="Agent@Example.COM",
        password="unused",
        name="Normalized",
    )
    # Django normalize_email lowercases the domain portion.
    assert user.email == "Agent@example.com"


@pytest.mark.django_db
def test_create_user_with_admin_role():
    user = User.objects.create_user(
        email="lead@example.com",
        password="unused",
        name="Lead Agent",
        role=UserRole.ADMIN,
    )
    assert user.role == UserRole.ADMIN
    assert not user.is_superuser


@pytest.mark.django_db
def test_create_superuser_rejects_non_staff():
    with pytest.raises(ValueError, match="is_staff"):
        User.objects.create_superuser(
            email="bad-admin@example.com",
            name="Bad Admin",
            is_staff=False,
        )


# --- Read ---


@pytest.mark.django_db
def test_get_user_by_email():
    User.objects.create_user(
        email="lookup@example.com",
        password="unused",
        name="Lookup User",
    )
    loaded = User.objects.get(email="lookup@example.com")
    assert loaded.name == "Lookup User"
    assert loaded.role == UserRole.AGENT


@pytest.mark.django_db
def test_str_returns_email():
    user = User.objects.create_user(
        email="str@example.com",
        password="unused",
        name="String User",
    )
    assert str(user) == "str@example.com"


# --- Update ---


@pytest.mark.django_db
def test_update_user_name_and_role():
    user = User.objects.create_user(
        email="update@example.com",
        password="unused",
        name="Before",
        role=UserRole.AGENT,
    )

    user.name = "After"
    user.role = UserRole.ADMIN
    user.save(update_fields=["name", "role"])
    user.refresh_from_db()

    assert user.name == "After"
    assert user.role == UserRole.ADMIN


@pytest.mark.django_db
def test_update_password():
    user = User.objects.create_user(
        email="pwd@example.com",
        password="OldPass!23",
        name="Password User",
    )
    user.set_password("NewPass!23")
    user.save(update_fields=["password"])
    user.refresh_from_db()

    assert user.check_password("NewPass!23")
    assert not user.check_password("OldPass!23")


@pytest.mark.django_db
def test_deactivate_user():
    user = User.objects.create_user(
        email="inactive@example.com",
        password="unused",
        name="Soon Inactive",
    )
    user.is_active = False
    user.save(update_fields=["is_active"])
    user.refresh_from_db()
    assert user.is_active is False


# --- Delete ---


@pytest.mark.django_db
def test_delete_user_without_related_records():
    user = User.objects.create_user(
        email="deleteme@example.com",
        password="unused",
        name="Delete Me",
    )
    user_id = user.id
    user.delete()
    assert not User.objects.filter(pk=user_id).exists()


# --- Constraints ---


@pytest.mark.django_db
def test_email_must_be_unique():
    User.objects.create_user(
        email="dup@example.com",
        password="unused",
        name="First",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user(
                email="dup@example.com",
                password="unused",
                name="Second",
            )
    assert User.objects.filter(email="dup@example.com").count() == 1


@pytest.mark.django_db
def test_invalid_role_rejected_by_check_constraint():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create(
                email="bad-role@example.com",
                name="Bad Role",
                role="MANAGER",
            )
    assert User.objects.filter(email="bad-role@example.com").count() == 0
