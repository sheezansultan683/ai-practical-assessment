from django.contrib import admin

from .models import Comment, Ticket


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("created_by", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "priority",
        "created_by",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority")
    search_fields = ("title", "description")
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "created_by", "created_at")
    search_fields = ("message",)
