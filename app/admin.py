from django.contrib import admin

from .models import Board, Category, Column, Task, TaskEvent


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name',)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'position', 'color')
    list_filter = ('board',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'color')
    list_filter = ('board',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'title', 'board', 'column', 'category', 'priority', 'assignee', 'created_at')
    list_filter = ('board', 'column', 'category', 'priority', 'assignee')
    search_fields = ('title', 'description')


@admin.register(TaskEvent)
class TaskEventAdmin(admin.ModelAdmin):
    """The audit trail is read-only: entries are written by the app, never edited by hand."""

    list_display = ('created_at', 'ticket', 'task_title', 'event_type', 'actor', 'board')
    list_filter = ('event_type', 'board')
    search_fields = ('ticket', 'task_title')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
