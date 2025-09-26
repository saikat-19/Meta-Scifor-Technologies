from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'resumes'  # This is the app namespace

urlpatterns = [
    # Resume CRUD - without 'resumes/' prefix for root inclusion
    path('list/', views.ResumeListView.as_view(), name='resume_list'),
    path('create/', views.ResumeCreateView.as_view(), name='resume_create'),
    path('<uuid:pk>/', views.ResumeDetailView.as_view(), name='resume_detail'),
    path('<uuid:pk>/delete/', views.ResumeDeleteView.as_view(), name='resume_delete'),
    path('<uuid:pk>/delete-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    
    # Print view
    path('<uuid:pk>/print/', views.ResumePrintView.as_view(), name='resume_print'),
    
    # Legacy URL for backward compatibility
    path('legacy/create/', views.create_resume, name='create_resume_legacy'),
]
