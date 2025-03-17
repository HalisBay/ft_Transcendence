from django.urls import path, re_path
from . import views

urlpatterns = [
    path("pong", views.pong, name="pong"),
    path("home", views.gameHome, name="gameHome"),
    path("profile/<int:user_id>", views.profile_view, name="profile_view"),
    path("tournament", views.tournamentRoom, name="tournamentRoom"),

    path("tournament/check-alias/", views.check_alias, name="check_alias"),
    path("home/check-active-game/", views.check_active_game, name="check_active_game"), 
]
