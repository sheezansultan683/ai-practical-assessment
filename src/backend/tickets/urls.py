from django.urls import path

from tickets.views import (
    TicketCommentCreateView,
    TicketDetailUpdateView,
    TicketExportView,
    TicketListCreateView,
    TicketTransitionView,
)

urlpatterns = [
    path("tickets/export/", TicketExportView.as_view(), name="ticket-export"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path(
        "tickets/<int:pk>/",
        TicketDetailUpdateView.as_view(),
        name="ticket-detail",
    ),
    path(
        "tickets/<int:pk>/transition/",
        TicketTransitionView.as_view(),
        name="ticket-transition",
    ),
    path(
        "tickets/<int:pk>/comments/",
        TicketCommentCreateView.as_view(),
        name="ticket-comments",
    ),
]
