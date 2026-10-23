from django.urls import path

from . import views

urlpatterns = [
    path('', views.board_list, name='board-list'),
    path('create/', views.board_create, name='board-create'),
    path('<int:pk>/', views.board_detail, name='board-detail'),
    path('<int:board_pk>/tasks/create/', views.task_create, name='task-create'),
    path('tasks/<int:pk>/update/', views.task_update, name='task-update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task-delete'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task-edit'),
    path('<int:board_pk>/columns/create/', views.column_create, name='column-create'),
    path('columns/<int:pk>/edit/', views.column_edit, name='column-edit'),
    path('columns/<int:pk>/delete/', views.column_delete, name='column-delete'),
    path('<int:board_pk>/categories/create/', views.category_create, name='category-create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category-edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category-delete'),
]
