from .models import Board


def sidebar_boards(request):
    """Expose the signed-in user's boards to the sidebar on every page."""
    if not request.user.is_authenticated:
        return {}
    return {'sidebar_boards': Board.objects.filter(owner=request.user)}
