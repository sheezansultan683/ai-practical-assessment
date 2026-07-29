from django.contrib.auth import get_user_model
from rest_framework import serializers

from tickets.models import Comment, Ticket, TicketPriority, TicketStatus
from tickets.services import allowed_transitions
from users.serializers import UserSerializer

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    ticket_id = serializers.IntegerField(source="ticket.id", read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "ticket_id", "message", "created_by", "created_at")
        read_only_fields = ("id", "ticket_id", "created_by", "created_at")


class CommentCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)

    def validate_message(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("This field may not be blank.")
        return cleaned


class TicketListSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            "id",
            "title",
            "description",
            "priority",
            "status",
            "assigned_to",
            "created_by",
            "created_at",
            "updated_at",
            "allowed_transitions",
        )
        read_only_fields = fields

    def get_allowed_transitions(self, obj: Ticket) -> list[str]:
        return allowed_transitions(obj.status)


class TicketDetailSerializer(TicketListSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + ("comments",)


class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=5000)
    priority = serializers.ChoiceField(choices=TicketPriority.choices)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )

    def validate_title(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("This field may not be blank.")
        return cleaned

    def validate_description(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("This field may not be blank.")
        return cleaned


class TicketUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(max_length=5000, required=False)
    priority = serializers.ChoiceField(
        choices=TicketPriority.choices,
        required=False,
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    status = serializers.CharField(required=False)

    def validate_title(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("This field may not be blank.")
        return cleaned

    def validate_description(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("This field may not be blank.")
        return cleaned

    def validate(self, attrs):
        if "status" in self.initial_data:
            raise serializers.ValidationError(
                {
                    "status": [
                        "Use POST /api/tickets/{id}/transition/ to change status."
                    ]
                },
                code="invalid",
            )
        return attrs


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TicketStatus.choices)
