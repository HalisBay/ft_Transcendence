from django.urls import path
from django.urls import re_path 
from django.views.generic import TemplateView
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('home', views.home_page, name='home'), 
    path('register', views.register_user, name='register'),
    path('login', views.login_user, name='login'),
    path('activate/<uidb64>/<token>/', views.activate_user, name='activate'),
    path('user', views.user_page, name='user'),
    path('logout', views.logout_page, name='logout'),

]