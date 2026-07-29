import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tickets.models import Comment, Ticket, TicketPriority, TicketStatus
from users.models import UserRole


User = get_user_model()

SEED_USERS = (
    {
        "email": "priya.nair@example.com",
        "name": "Priya Nair",
        "role": UserRole.AGENT,
    },
    {
        "email": "james.okonkwo@example.com",
        "name": "James Okonkwo",
        "role": UserRole.AGENT,
    },
    {
        "email": "sara.chen@example.com",
        "name": "Sara Chen",
        "role": UserRole.ADMIN,
    },
)


class Command(BaseCommand):
    help = (
        "Idempotently seed demo users, tickets across all statuses/priorities, "
        "and sample comments."
    )

    def handle(self, *args, **options):
        password = os.environ.get("SEED_PASSWORD")
        if not password:
            raise CommandError(
                "SEED_PASSWORD is required in the environment (see .env.example)."
            )

        with transaction.atomic():
            users = self._seed_users(password)
            tickets = self._seed_tickets(users)
            self._seed_comments(users, tickets)

        self.stdout.write(self.style.SUCCESS("Seed completed (idempotent)."))

    def _seed_users(self, password):
        users = {}
        for spec in SEED_USERS:
            user, created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "name": spec["name"],
                    "role": spec["role"],
                },
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
                self.stdout.write(f"Created user {user.email}")
            else:
                # Keep identity fields aligned with the seed spec without
                # resetting passwords on re-runs (superuser/local edits stay).
                dirty = False
                if user.name != spec["name"]:
                    user.name = spec["name"]
                    dirty = True
                if user.role != spec["role"]:
                    user.role = spec["role"]
                    dirty = True
                if dirty:
                    user.save(update_fields=["name", "role"])
                self.stdout.write(f"User exists {user.email}")
            users[spec["email"]] = user
        return users

    def _seed_tickets(self, users):
        priya = users["priya.nair@example.com"]
        james = users["james.okonkwo@example.com"]
        sara = users["sara.chen@example.com"]

        specs = (
            {
                "title": "[seed] VPN disconnects every hour",
                "description": (
                    "Since the Friday firewall change, remote staff lose VPN "
                    "after about 60 minutes."
                ),
                "priority": TicketPriority.HIGH,
                "status": TicketStatus.OPEN,
                "created_by": james,
                "assigned_to": priya,
            },
            {
                "title": "[seed] Printer queue stuck on floor 3",
                "description": "Jobs sit in Pending and never reach the device.",
                "priority": TicketPriority.MEDIUM,
                "status": TicketStatus.IN_PROGRESS,
                "created_by": priya,
                "assigned_to": james,
            },
            {
                "title": "[seed] Password reset email delayed",
                "description": "Reset links arrive after 10+ minutes for some users.",
                "priority": TicketPriority.LOW,
                "status": TicketStatus.RESOLVED,
                "created_by": sara,
                "assigned_to": priya,
            },
            {
                "title": "[seed] Laptop docking station intermittent",
                "description": "HDMI and USB-C drop when lid is closed.",
                "priority": TicketPriority.MEDIUM,
                "status": TicketStatus.CLOSED,
                "created_by": james,
                "assigned_to": sara,
            },
            {
                "title": "[seed] Duplicate calendar invites from booking tool",
                "description": "Cancelled — duplicate of existing calendar bug.",
                "priority": TicketPriority.LOW,
                "status": TicketStatus.CANCELLED,
                "created_by": priya,
                "assigned_to": None,
            },
            {
                "title": "[seed] Unassigned Wi-Fi drop in east wing",
                "description": "Untriaged report waiting for an assignee.",
                "priority": TicketPriority.HIGH,
                "status": TicketStatus.OPEN,
                "created_by": sara,
                "assigned_to": None,
            },
        )

        tickets = {}
        for spec in specs:
            ticket, created = Ticket.objects.get_or_create(
                title=spec["title"],
                created_by=spec["created_by"],
                defaults={
                    "description": spec["description"],
                    "priority": spec["priority"],
                    "status": spec["status"],
                    "assigned_to": spec["assigned_to"],
                },
            )
            if not created:
                # Re-align mutable seed fields without creating duplicates.
                ticket.description = spec["description"]
                ticket.priority = spec["priority"]
                ticket.status = spec["status"]
                ticket.assigned_to = spec["assigned_to"]
                ticket.save(
                    update_fields=[
                        "description",
                        "priority",
                        "status",
                        "assigned_to",
                        "updated_at",
                    ]
                )
                self.stdout.write(f"Ticket exists {ticket.title}")
            else:
                self.stdout.write(f"Created ticket {ticket.title}")
            tickets[spec["title"]] = ticket
        return tickets

    def _seed_comments(self, users, tickets):
        priya = users["priya.nair@example.com"]
        james = users["james.okonkwo@example.com"]

        specs = (
            {
                "ticket_title": "[seed] VPN disconnects every hour",
                "message": "Reproduced on two laptops after the firewall change.",
                "created_by": james,
            },
            {
                "ticket_title": "[seed] Printer queue stuck on floor 3",
                "message": "Cleared spooler once; issue returned within an hour.",
                "created_by": priya,
            },
            {
                "ticket_title": "[seed] Laptop docking station intermittent",
                "message": "Closed after firmware update — leaving note for audit.",
                "created_by": james,
            },
        )

        for spec in specs:
            ticket = tickets[spec["ticket_title"]]
            comment, created = Comment.objects.get_or_create(
                ticket=ticket,
                message=spec["message"],
                created_by=spec["created_by"],
            )
            if created:
                self.stdout.write(f"Created comment on {ticket.title}")
            else:
                self.stdout.write(f"Comment exists on {ticket.title}")
