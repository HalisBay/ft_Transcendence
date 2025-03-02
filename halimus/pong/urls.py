from django.urls import path, re_path
from . import views

urlpatterns = [
    path("pong", views.pong, name="pong"),
    path("home", views.gameHome, name="gameHome"),
    path("profile/<int:user_id>", views.profile_view, name="profile_view"),
    path("tournament", views.tournamentRoom, name="tournamentRoom"),
]
