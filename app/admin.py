from django.contrib import admin

from .models import Board, Column, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name',)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'position', 'color')
    list_filter = ('board',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'board', 'column', 'priority', 'assignee', 'created_at')
    list_filter = ('board', 'column', 'priority', 'assignee')
    search_fields = ('title', 'description')
