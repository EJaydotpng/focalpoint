import re

from django.db import models
from django.contrib.auth.models import User


def default_prefix(name):
    """Derive a short ticket prefix from a board name ("Product Team" -> "PT")."""
    words = re.findall(r'[A-Za-z0-9]+', name or '')
    if len(words) >= 2:
        prefix = ''.join(w[0] for w in words)[:4]
    elif words:
        prefix = words[0][:3]
    else:
        prefix = 'TSK'
    return prefix.upper()


class Board(models.Model):
    """A Kanban board owned by a user."""

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    prefix = models.CharField(max_length=6, default='TSK')
    ticket_counter = models.PositiveIntegerField(default=0)
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


class Category(models.Model):
    """A user-made label for tasks on a board (e.g. Bug, Design, Research)."""

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='#e5e7eb')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
        unique_together = [('board', 'name')]

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
    number = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks'
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['board', 'column', 'position']
        unique_together = [('board', 'number')]

    @property
    def ticket_id(self):
        return f'{self.board.prefix}-{self.number}'

    def __str__(self):
        return self.title
