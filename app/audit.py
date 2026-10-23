"""Helpers that record a task's audit trail (see models.TaskEvent)."""

from .models import Task, TaskEvent

# The task fields that are tracked, in the order they are shown.
EDIT_FIELDS = ['Title', 'Description', 'Priority', 'Assignee', 'Category']


def snapshot(task):
    """The tracked, human-readable values of a task right now."""
    task = Task.objects.select_related('assignee', 'category', 'column').get(pk=task.pk)
    return {
        'Title': task.title,
        'Description': task.description,
        'Priority': task.get_priority_display(),
        'Assignee': task.assignee.username if task.assignee_id else '',
        'Category': task.category.name if task.category_id else '',
        'Column': task.column.name,
    }


def diff(old, new, fields):
    return [
        {'field': f, 'from': old[f], 'to': new[f]}
        for f in fields
        if old[f] != new[f]
    ]


def record(task, event_type, actor, changes=None, note=''):
    return TaskEvent.objects.create(
        board=task.board,
        task=task,
        ticket=f'{task.board.prefix}-{task.number}',
        task_title=task.title,
        actor=actor,
        event_type=event_type,
        changes=changes or [],
        note=note,
    )


def record_created(task, actor):
    values = snapshot(task)
    changes = [
        {'field': f, 'from': None, 'to': values[f]}
        for f in ['Column', 'Priority', 'Assignee', 'Category', 'Description']
        if values[f]
    ]
    return record(task, TaskEvent.CREATED, actor, changes)


def record_edit(task, old, actor):
    """Log what changed between `old` (a snapshot) and now: an edit, a move, or both."""
    new = snapshot(task)
    edits = diff(old, new, EDIT_FIELDS)
    if edits:
        record(task, TaskEvent.EDITED, actor, edits)
    moves = diff(old, new, ['Column'])
    if moves:
        record(task, TaskEvent.MOVED, actor, moves)


def record_deleted(task, actor, note=''):
    column = task.column.name
    return record(task, TaskEvent.DELETED, actor, [{'field': 'Column', 'from': column, 'to': None}], note)
