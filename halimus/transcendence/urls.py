from django.urls import path
from django.urls import re_path 
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('home', views.home_page, name='home'), 
    path('register', views.register_user, name='register'),
    path('login', views.login_page, name='login'), 
    path('user', views.user_page, name='user'),
]