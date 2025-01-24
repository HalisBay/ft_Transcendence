from django.urls import path,re_path
from . import views

urlpatterns = [
    path('', views.friend_list, name='friend_list'),
    path('send_request', views.send_friend_request, name='send_friend_request'),
    path('accept_request/<int:request_id>', views.accept_friend_request, name='accept_friend_request'),
    path('reject_request/<int:request_id>', views.reject_friend_request, name='reject_friend_request'),
]