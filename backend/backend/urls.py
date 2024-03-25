# urls.py
from django.contrib.auth.views import LoginView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('create_seed_list/', views.create_seed_list, name='create_seed_list'),
    path('display_seed_list/<int:id>/', views.display_seed_list, name='display_seed_list'),
    path('delete_seed_list/<int:seed_list_id>/', views.delete_seed_list, name='delete_seed_list'),
    path('create_bracket/', views.create_bracket_form, name='create_bracket'),
    path('create_bracket/<int:seed_list_id>/', views.create_bracket, name='create_bracket'),
    path('create_first_four/', views.create_first_four, name='create_first_four'),
    path('display_bracket/<int:id>/', views.display_bracket, name='display_bracket'),
    path('create_live_bracket/', views.create_live_bracket, name='create_live_bracket'),
    path('create_live_bracket/<int:game_number>/', views.create_live_bracket, name='create_live_bracket'),
    path('delete_bracket/<int:id>/', views.delete_bracket, name='delete_bracket'),
]