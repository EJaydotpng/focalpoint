from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """A Kanban board owned by a user."""

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Column(models.Model):
    """A Kanban swimlane on a board (e.g. To Do, In Progress, Done)."""

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=20, default='#ccc')

    class Meta:
        ordering = ['board', 'position']
        unique_together = [('board', 'position')]

    def __str__(self):
        return self.name


class Task(models.Model):
    """A task card inside a column."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks')
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks'
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['board', 'column', 'position']

    def __str__(self):
        return self.title
