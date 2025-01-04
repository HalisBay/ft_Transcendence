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
    path('activate/<str:uidb64>/<str:token>/', views.activate_user, name='activate_user'),
    path('verify', views.verify_page, name='verify_page'),
    path('user', views.user_page, name='user'),
    path('logout', views.logout_page, name='logout'),
    path('notverified', views.verify_fail, name='not_verified'),
    path('user/activate2fa', views.activate_2fa, name='user_2fa'),
]