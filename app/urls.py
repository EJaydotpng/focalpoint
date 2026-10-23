from django.urls import path

from . import views

urlpatterns = [
    path('', views.board_list, name='board-list'),
    path('create/', views.board_create, name='board-create'),
    path('<int:pk>/', views.board_detail, name='board-detail'),
    path('<int:board_pk>/tasks/create/', views.task_create, name='task-create'),
    path('tasks/<int:pk>/update/', views.task_update, name='task-update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task-delete'),
]
