from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.ProjectListView.as_view(), name='home'),
    path('about/', views.about, name="about"),
    path('usage_agreement/', views.usage_agreement, name='usage_agreement'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('delete_profile/', views.delete_profile, name='delete_profile'),
    path('profile/', views.user_profile, name='user_profile'),
    path('logout/', views.user_logout, name='logout'),
    path('create-project/', views.create_project, name='create_project'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('friends/', views.FriendsView.as_view(), name='friends_list'),
    path('delete_friend/<int:friend_id>/', views.delete_friend, name='delete_friend'),
    path('friends/', views.FriendsView.as_view(), name='friends_list'),
    path('confirm_friend_request/<int:request_id>/', views.handle_friend_request, name='confirm_friend_request'),
    path('delete_friend_request/<int:request_id>/', views.delete_friend, name='delete_friend_request'),
    path('project/<int:project_id>/create-task/', views.create_task, name='create_task'),
    path('task/edit/<int:pk>/', views.EditTaskView.as_view(), name='edit_task'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/cancel/', views.cancel_task, name='cancel_task'),

]