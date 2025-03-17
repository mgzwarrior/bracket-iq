# urls.py
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import admin
from django.urls import path, include
from . import views
from .admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),  # Use our custom admin site
    path('', views.home, name='home'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    
    # Bracket URLs
    path('bracket/create/', views.create_bracket_form, name='create_bracket_form'),  # Form to select tournament
    path('bracket/create/<int:tournament_id>/', views.create_bracket, name='create_bracket'),  # Create bracket for specific tournament
    path('bracket/<int:bracket_id>/', views.display_bracket, name='display_bracket'),
    path('bracket/<int:bracket_id>/delete/', views.delete_bracket, name='delete_bracket'),
    path('bracket/prediction/<int:prediction_id>/update/', views.update_prediction, name='update_prediction'),
    path('brackets/', views.list_brackets, name='list_brackets'),
    path('bracket/live/create/', views.create_live_bracket, name='create_live_bracket'),  # Add live bracket creation
    path('bracket/live/create/<int:game_number>/', views.create_live_bracket, name='create_live_bracket'),  # Add live bracket creation with game number
    
    # Password Reset URLs with template names specified
    path('password_reset/', PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]