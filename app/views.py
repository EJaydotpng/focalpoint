from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Board, Column, Task


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
        board = Board.objects.create(name=name, owner=request.user)
        # Seed default JIRA-ish columns.
        Column.objects.create(board=board, name='To Do', position=0, color='#edeff2')
        Column.objects.create(board=board, name='In Progress', position=1, color='#f8c291')
        Column.objects.create(board=board, name='Done', position=2, color='#87b5a5')
        return redirect('board-detail', pk=board.pk)
    return render(request, 'app/board_create.html')


@login_required
def board_detail(request, pk):
    board = get_object_or_404(Board, pk=pk, owner=request.user)
    columns = board.columns.all()
    users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'app/board_detail.html', {
        'board': board,
        'columns': columns,
        'users': users,
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
        Task.objects.create(
            board=board,
            column=column,
            title=title,
            description=request.POST.get('description', ''),
            priority=request.POST.get('priority', 'medium'),
            assignee_id=request.POST.get('assignee') or None,
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
