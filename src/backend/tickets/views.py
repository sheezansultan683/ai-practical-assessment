import csv

from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import TicketPagination
from config.schema import (
    AUTH_401,
    CONFLICT_409,
    NOT_FOUND_404,
    VALIDATION_400,
    paginated_ticket_list_serializer,
)
from tickets.filters import TicketFilter
from tickets.models import Comment, Ticket
from tickets.serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketUpdateSerializer,
    TransitionSerializer,
)
from tickets.services import (
    add_comment,
    create_ticket,
    transition_ticket,
    update_ticket_fields,
)

TICKET_FILTER_PARAMS = [
    OpenApiParameter(
        name="status",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Filter by status (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `CANCELLED`).",
        enum=["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", "CANCELLED"],
    ),
    OpenApiParameter(
        name="priority",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Filter by priority (`LOW`, `MEDIUM`, `HIGH`).",
        enum=["LOW", "MEDIUM", "HIGH"],
    ),
    OpenApiParameter(
        name="assigned_to",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Filter by assignee user id.",
    ),
    OpenApiParameter(
        name="q",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description=(
            "Case-insensitive search on title or description "
            "(max 200 chars). Empty or omitted = no search."
        ),
    ),
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Page number (default 1).",
    ),
    OpenApiParameter(
        name="page_size",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Page size (default 20, max 100).",
    ),
]


@extend_schema_view(
    get=extend_schema(
        tags=["Tickets"],
        summary="List tickets",
        description=(
            "List all tickets with optional status/priority/assignee filters, "
            "free-text search (`q`), and page-number pagination. "
            "Default order is newest first (`-created_at`). "
            "List items do not embed comments."
        ),
        parameters=TICKET_FILTER_PARAMS,
        responses={
            200: paginated_ticket_list_serializer(),
            400: VALIDATION_400,
            401: AUTH_401,
            404: NOT_FOUND_404,
        },
    ),
    post=extend_schema(
        tags=["Tickets"],
        summary="Create ticket",
        description=(
            "Create a ticket. Status always starts as `OPEN`; "
            "`created_by` is always the authenticated user. "
            "Client-supplied `created_by` / `status` are ignored or rejected."
        ),
        request=TicketCreateSerializer,
        responses={
            201: TicketDetailSerializer,
            400: VALIDATION_400,
            401: AUTH_401,
        },
    ),
)
class TicketListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TicketPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TicketFilter

    def get_queryset(self):
        return Ticket.objects.select_related("assigned_to", "created_by").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListSerializer

    def list(self, request, *args, **kwargs):
        filterset = self.filterset_class(
            data=request.query_params,
            queryset=self.get_queryset(),
            request=request,
        )
        if not filterset.is_valid():
            raise ValidationError(filterset.errors)
        self.filterset = filterset
        return super().list(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        if hasattr(self, "filterset"):
            return self.filterset.qs
        return super().filter_queryset(queryset)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = create_ticket(
            created_by=request.user,
            title=serializer.validated_data["title"],
            description=serializer.validated_data["description"],
            priority=serializer.validated_data["priority"],
            assigned_to=serializer.validated_data.get("assigned_to"),
        )
        ticket = (
            Ticket.objects.select_related("assigned_to", "created_by")
            .prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("created_by"),
                )
            )
            .get(pk=ticket.pk)
        )
        return Response(
            TicketDetailSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Tickets"],
        summary="Get ticket detail",
        description="Return a ticket with nested comments and allowed_transitions.",
        responses={
            200: TicketDetailSerializer,
            401: AUTH_401,
            404: NOT_FOUND_404,
        },
    ),
    patch=extend_schema(
        tags=["Tickets"],
        summary="Update ticket fields",
        description=(
            "Partial update of title, description, priority, and/or assigned_to. "
            "Do not send `status` — use the transition endpoint. "
            "Field updates on CLOSED or CANCELLED tickets return 409."
        ),
        request=TicketUpdateSerializer,
        responses={
            200: TicketDetailSerializer,
            400: VALIDATION_400,
            401: AUTH_401,
            404: NOT_FOUND_404,
            409: CONFLICT_409,
        },
    ),
)
class TicketDetailUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Ticket.objects.select_related(
            "assigned_to",
            "created_by",
        ).prefetch_related(
            Prefetch(
                "comments",
                queryset=Comment.objects.select_related("created_by"),
            )
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        return Response(TicketDetailSerializer(ticket).data)

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        serializer = TicketUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_ticket_fields(ticket, **serializer.validated_data)
        ticket = self.get_queryset().get(pk=ticket.pk)
        return Response(TicketDetailSerializer(ticket).data)


class TicketTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Tickets"],
        summary="Transition ticket status",
        description=(
            "Change status via the server allow-list only. "
            "Invalid transitions (including same-status and reopen) return 409 "
            "with current, attempted, and allowed alternatives. "
            "Unknown status strings return 400."
        ),
        request=TransitionSerializer,
        responses={
            200: TicketDetailSerializer,
            400: VALIDATION_400,
            401: AUTH_401,
            404: NOT_FOUND_404,
            409: CONFLICT_409,
        },
    )
    def post(self, request, pk):
        try:
            ticket = (
                Ticket.objects.select_related("assigned_to", "created_by")
                .prefetch_related(
                    Prefetch(
                        "comments",
                        queryset=Comment.objects.select_related("created_by"),
                    )
                )
                .get(pk=pk)
            )
        except Ticket.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": "Not found.",
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = transition_ticket(ticket, serializer.validated_data["status"])
        ticket = (
            Ticket.objects.select_related("assigned_to", "created_by")
            .prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("created_by"),
                )
            )
            .get(pk=ticket.pk)
        )
        return Response(TicketDetailSerializer(ticket).data)


class TicketCommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Tickets"],
        summary="Add comment",
        description=(
            "Append a comment to a ticket. Allowed on any status, including "
            "terminal (CLOSED / CANCELLED). Comments are append-only."
        ),
        request=CommentCreateSerializer,
        responses={
            201: CommentSerializer,
            400: VALIDATION_400,
            401: AUTH_401,
            404: NOT_FOUND_404,
        },
    )
    def post(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": "Not found.",
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = add_comment(
            ticket=ticket,
            created_by=request.user,
            message=serializer.validated_data["message"],
        )
        comment = Comment.objects.select_related("created_by").get(pk=comment.pk)
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )


class TicketExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Tickets"],
        summary="Export own tickets as CSV",
        description=(
            "Download a CSV of tickets where `created_by` is the authenticated user. "
            "Never includes other users' tickets. Header-only CSV when the user "
            "has none. Columns: id, title, description, priority, status, "
            "assigned_to_id, assigned_to_email, created_by_id, created_by_email, "
            "created_at, updated_at, comment_count."
        ),
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="CSV file (`text/csv; charset=utf-8`).",
            ),
            401: AUTH_401,
        },
    )
    def get(self, request):
        queryset = (
            Ticket.objects.filter(created_by=request.user)
            .select_related("assigned_to", "created_by")
            .annotate(comment_count=Count("comments"))
            .order_by("-created_at")
        )

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="my_tickets.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "title",
                "description",
                "priority",
                "status",
                "assigned_to_id",
                "assigned_to_email",
                "created_by_id",
                "created_by_email",
                "created_at",
                "updated_at",
                "comment_count",
            ]
        )
        for ticket in queryset:
            writer.writerow(
                [
                    ticket.id,
                    ticket.title,
                    ticket.description,
                    ticket.priority,
                    ticket.status,
                    ticket.assigned_to_id or "",
                    getattr(ticket.assigned_to, "email", "") or "",
                    ticket.created_by_id,
                    ticket.created_by.email,
                    ticket.created_at.isoformat().replace("+00:00", "Z"),
                    ticket.updated_at.isoformat().replace("+00:00", "Z"),
                    ticket.comment_count,
                ]
            )
        return response
