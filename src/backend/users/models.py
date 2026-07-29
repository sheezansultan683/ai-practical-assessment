from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class UserRole(models.TextChoices):
    AGENT = "AGENT", "Agent"
    ADMIN = "ADMIN", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.AGENT,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=UserRole.values),
                name="user_role_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.email
