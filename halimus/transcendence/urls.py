from django.urls import path
from . import views

urlpatterns = [
    path('register/',views.register_page),
    path('save-regi/', views.register_user, name='halis'),
    path('', views.register_user, name='halis2')

]