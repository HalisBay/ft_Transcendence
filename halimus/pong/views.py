from django.shortcuts import render, get_object_or_404
from transcendence.requireds import jwt_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .models import MatchHistory
from django.contrib.auth import get_user_model
from pong.models import User
from pong.consumers import rooms

@login_required
@jwt_required
def pong(request):
    return render(request, 'pages/index2.html')

@login_required
@jwt_required
def gameHome(request):
    return render(request, 'pages/gameHome.html')

@login_required
@jwt_required
def tournamentRoom(request):
    return render(request, 'pages/tRoom.html')

User = get_user_model()
@login_required
def profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    match_history = MatchHistory.objects.filter(user=user).select_related('opponent').order_by('-date_time')

    match_details = [
        {
            'opponent': match.opponent.nick,
            'user_score': match.score,
            'opponent_score': (
                match.opponent_score
            ),
            'result': match.result,
            'date_time': match.date_time,
            'tWinner': match.tWinner
        }
        for match in match_history
    ]

    context = {
        'profile_user': user,
        'match_details': match_details,
        'total_matches': match_history.count(),
        'total_wins': match_history.filter(result=True).count(),
        'total_losses': match_history.filter(result=False).count(),
        'tWinner': match_history
    }
    return render(request, 'pages/profile.html', context)



def check_alias(request):
    alias = request.GET.get("alias")
    print("buraya geldi mi ki")
    # Turnuvadaki tüm alias'ları kontrol et
    active_aliases = set()
    for room_name, room_data in rooms.items():
        if room_name.startswith("tournament_"):  # Sadece turnuva odalarına bak
            for player in room_data["players"]:
                if player.alias:  # Eğer alias boş değilse ekle
                    active_aliases.add(player.alias)

    # Alias turnuvada var mı?
    return JsonResponse({"exists": alias in active_aliases})


# Sunucu tarafında kullanıcının aktif bir oyunda olup olmadığını kontrol eden endpoint
def check_active_game(request):
    print("CHECK ACTIVE GAME")
    user = request.user
    in_game = any(user in room["players"] for room in rooms.values())
    return JsonResponse({"in_game": in_game})
