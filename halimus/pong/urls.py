from django.urls import path
from . import views

urlpatterns = [
    path('pong', views.pong, name ='pong'), #TODO: MUSTAFA BURAYI AYARLA 
    path('home', views.gameHome, name = 'gameHome')
]
