from django.db.models import Q
from django_filters import rest_framework as filters

from tickets.models import Ticket, TicketPriority, TicketStatus


class TicketFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=TicketStatus.choices)
    priority = filters.ChoiceFilter(choices=TicketPriority.choices)
    assigned_to = filters.NumberFilter(field_name="assigned_to_id")
    q = filters.CharFilter(method="filter_q", max_length=200)

    class Meta:
        model = Ticket
        fields = ("status", "priority", "assigned_to")

    def filter_q(self, queryset, name, value):
        cleaned = (value or "").strip()
        if not cleaned:
            return queryset
        return queryset.filter(
            Q(title__icontains=cleaned) | Q(description__icontains=cleaned)
        )
