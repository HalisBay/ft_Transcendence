from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('home', views.home_page, name='home'), 
    path('register', views.register_user, name='register'),
    path('login', views.login_page, name='login'), 
]