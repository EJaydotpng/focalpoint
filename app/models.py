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


class TaskEvent(models.Model):
    """One entry in a task's audit trail.

    Everything a reader needs is stored as text snapshots (ticket, title, column
    names, usernames) so the history stays accurate after things are renamed,
    and survives the task itself being deleted.
    """

    CREATED = 'created'
    MOVED = 'moved'
    EDITED = 'edited'
    DELETED = 'deleted'
    TYPE_CHOICES = [
        (CREATED, 'Created'),
        (MOVED, 'Moved'),
        (EDITED, 'Edited'),
        (DELETED, 'Deleted'),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='events')
    task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.SET_NULL, related_name='events')
    ticket = models.CharField(max_length=30)
    task_title = models.CharField(max_length=200)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='task_events')
    event_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    # [{"field": "Priority", "from": "Low", "to": "High"}, ...]  (None = not set)
    changes = models.JSONField(default=list, blank=True)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return f'{self.ticket} {self.event_type}'

    # ----- Human-readable description, shared by the JSON endpoint and the activity page -----

    @staticmethod
    def _show(value, limit=80):
        if value is None or value == '':
            return 'none'
        value = str(value).replace('\n', ' ')
        return value if len(value) <= limit else value[: limit - 1] + '\u2026'

    def _change(self, field):
        for change in self.changes:
            if change.get('field') == field:
                return change
        return None

    @property
    def headline(self):
        column = self._change('Column')
        if self.event_type == self.CREATED:
            return f"Created in {column['to']}" if column and column.get('to') else 'Created'
        if self.event_type == self.MOVED and column:
            return f"Moved from {self._show(column.get('from'))} to {self._show(column.get('to'))}"
        if self.event_type == self.DELETED:
            return f"Deleted from {column['from']}" if column and column.get('from') else 'Deleted'
        return 'Edited'

    @property
    def detail_lines(self):
        lines = []
        for change in self.changes:
            field = change.get('field')
            old, new = change.get('from'), change.get('to')
            if field == 'Column' and self.event_type in (self.CREATED, self.MOVED, self.DELETED):
                continue  # already in the headline
            if old is None and self.event_type == self.CREATED:
                lines.append(f'{field}: {self._show(new)}')
            else:
                lines.append(f'{field}: {self._show(old)} \u2192 {self._show(new)}')
        if self.note:
            lines.append(self.note)
        return lines

    @property
    def actor_name(self):
        return self.actor.username if self.actor_id else 'Unknown user'
