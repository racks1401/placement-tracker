from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Job Applications
    path('applications/', views.application_list_view, name='application_list'),
    path('applications/new/', views.application_create_view, name='application_create'),
    path('applications/<int:pk>/', views.application_detail_view, name='application_detail'),
    path('applications/<int:pk>/edit/', views.application_update_view, name='application_update'),
    path('applications/<int:pk>/delete/', views.application_delete_view, name='application_delete'),

    # Target Companies
    path('companies/', views.company_list_view, name='company_list'),
    path('companies/new/', views.company_create_view, name='company_create'),
    path('companies/<int:pk>/edit/', views.company_update_view, name='company_update'),
    path('companies/<int:pk>/delete/', views.company_delete_view, name='company_delete'),

    # Resume Versions
    path('resumes/', views.resume_list_view, name='resume_list'),
    path('resumes/new/', views.resume_create_view, name='resume_create'),
    path('resumes/<int:pk>/edit/', views.resume_update_view, name='resume_update'),
    path('resumes/<int:pk>/delete/', views.resume_delete_view, name='resume_delete'),

    # Interview Rounds
    path('applications/<int:app_pk>/rounds/new/', views.round_create_view, name='round_create'),
    path('rounds/<int:pk>/edit/', views.round_update_view, name='round_update'),
    path('rounds/<int:pk>/delete/', views.round_delete_view, name='round_delete'),

    # Application Notes
    path('applications/<int:app_pk>/notes/new/', views.note_create_view, name='note_create'),
    path('notes/<int:pk>/delete/', views.note_delete_view, name='note_delete'),
]
