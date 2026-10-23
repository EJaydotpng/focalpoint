from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Board, Category, Column, Task, default_prefix

DEFAULT_COLUMN_COLOR = '#e5e7eb'
VALID_PRIORITIES = {value for value, _label in Task.PRIORITY_CHOICES}


COLUMN_SWATCHES = [
    ('#e5e7eb', 'Grey'),
    ('#bfdbfe', 'Blue'),
    ('#cdb8f5', 'Purple'),
    ('#fbcfe8', 'Pink'),
    ('#fecaca', 'Red'),
    ('#fcd9a8', 'Orange'),
    ('#fde68a', 'Yellow'),
    ('#a7e3c0', 'Green'),
]


def _clean_prefix(value, fallback_name):
    """Ticket prefix: letters and digits only, upper-case, up to 6 characters."""
    cleaned = ''.join(c for c in (value or '') if c.isalnum()).upper()[:6]
    return cleaned or default_prefix(fallback_name)


def _board_category(board, category_id):
    """Return the category if it belongs to this board, otherwise None."""
    if not category_id:
        return None
    return Category.objects.filter(pk=category_id, board=board).first()


def _clean_color(value):
    """Accept only #rrggbb values so the colour is safe to put in a style attribute."""
    value = (value or '').strip()
    if len(value) == 7 and value[0] == '#' and all(c in '0123456789abcdefABCDEF' for c in value[1:]):
        return value
    return DEFAULT_COLUMN_COLOR


@login_required
def board_list(request):
    boards = Board.objects.filter(owner=request.user)
    return render(request, 'app/board_list.html', {'boards': boards})


@login_required
def board_create(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if not name:
            return render(request, 'app/board_create.html', {'error': 'Board name is required.'})
        board = Board.objects.create(
            name=name,
            owner=request.user,
            prefix=_clean_prefix(request.POST.get('prefix'), name),
        )
        return redirect('board-detail', pk=board.pk)
    return render(request, 'app/board_create.html')


@login_required
def board_detail(request, pk):
    board = get_object_or_404(Board, pk=pk, owner=request.user)
    columns = board.columns.all()
    users = User.objects.order_by('username')
    return render(request, 'app/board_detail.html', {
        'board': board,
        'columns': columns,
        'users': users,
        'categories': board.categories.all(),
        'swatches': COLUMN_SWATCHES,
    })


@login_required
def task_create(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk, owner=request.user)
    if request.method == 'POST':
        column_id = request.POST.get('column')
        title = (request.POST.get('title') or '').strip()
        if not column_id or not title:
            return redirect('board-detail', pk=board.pk)
        column = get_object_or_404(Column, pk=column_id, board=board)
        last_position = Task.objects.filter(column=column).count()
        priority = request.POST.get('priority')
        with transaction.atomic():
            # Take the next ticket number for this board.
            Board.objects.filter(pk=board.pk).update(ticket_counter=F('ticket_counter') + 1)
            board.refresh_from_db(fields=['ticket_counter'])
            Task.objects.create(
                board=board,
                column=column,
                number=board.ticket_counter,
                title=title[:200],
                description=request.POST.get('description', ''),
                priority=priority if priority in VALID_PRIORITIES else 'medium',
                assignee_id=request.POST.get('assignee') or None,
                category=_board_category(board, request.POST.get('category')),
                position=last_position,
            )
    return redirect('board-detail', pk=board.pk)


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.board.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        column_id = request.POST.get('column')
        position = request.POST.get('position')
        if column_id:
            column = get_object_or_404(Column, pk=column_id, board=task.board)
            task.column = column
        if position is not None:
            try:
                task.position = int(position)
            except (TypeError, ValueError):
                pass
        task.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.board.owner != request.user:
        raise PermissionDenied
    board_pk = task.board.pk
    if request.method == 'POST':
        task.delete()
    return redirect('board-detail', pk=board_pk)


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.board.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        if title:
            task.title = title[:200]
            task.description = request.POST.get('description', '')
            priority = request.POST.get('priority')
            if priority in VALID_PRIORITIES:
                task.priority = priority
            task.assignee_id = request.POST.get('assignee') or None
            task.category = _board_category(task.board, request.POST.get('category'))
            column_id = request.POST.get('column')
            if column_id and str(task.column_id) != column_id:
                column = get_object_or_404(Column, pk=column_id, board=task.board)
                task.column = column
                # Moved by hand: put it at the bottom of the new column.
                task.position = column.tasks.count()
            task.save()
    return redirect('board-detail', pk=task.board.pk)


@login_required
def column_create(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk, owner=request.user)
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if name:
            last = board.columns.aggregate(last=Max('position'))['last']
            Column.objects.create(
                board=board,
                name=name[:100],
                color=_clean_color(request.POST.get('color')),
                position=0 if last is None else last + 1,
            )
    return redirect('board-detail', pk=board.pk)


@login_required
def column_edit(request, pk):
    column = get_object_or_404(Column, pk=pk)
    if column.board.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if name:
            column.name = name[:100]
            column.color = _clean_color(request.POST.get('color'))
            column.save()
    return redirect('board-detail', pk=column.board.pk)


@login_required
def column_delete(request, pk):
    column = get_object_or_404(Column, pk=pk)
    if column.board.owner != request.user:
        raise PermissionDenied
    board_pk = column.board.pk
    if request.method == 'POST':
        column.delete()  # its tasks go with it
    return redirect('board-detail', pk=board_pk)


@login_required
def category_create(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk, owner=request.user)
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:50]
        if name and not board.categories.filter(name__iexact=name).exists():
            Category.objects.create(
                board=board, name=name, color=_clean_color(request.POST.get('color'))
            )
    return redirect('board-detail', pk=board.pk)


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.board.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:50]
        taken = category.board.categories.filter(name__iexact=name).exclude(pk=category.pk).exists()
        if name and not taken:
            category.name = name
            category.color = _clean_color(request.POST.get('color'))
            category.save()
    return redirect('board-detail', pk=category.board.pk)


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.board.owner != request.user:
        raise PermissionDenied
    board_pk = category.board.pk
    if request.method == 'POST':
        category.delete()  # tasks keep existing, just uncategorised
    return redirect('board-detail', pk=board_pk)
