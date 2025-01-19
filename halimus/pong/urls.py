from django.urls import path,re_path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('pong', views.pong, name ='pong'), #TODO: MUSTAFA BURAYI AYARLA 
    path('home', views.gameHome, name = 'gameHome'),
    re_path(r'^.*$', TemplateView.as_view(template_name='pages/404.html'), name='page_not_found'),

]
