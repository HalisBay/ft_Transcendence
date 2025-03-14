from django.shortcuts import render
from transcendence.requireds import jwt_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Tournament
import json
@login_required
@jwt_required
def pong(request):
    return render(request, 'pages/index2.html')

@login_required
@jwt_required
def gameHome(request):
    return render(request, 'pages/gameHome.html')

from django.shortcuts import render
from .models import Tournament

@login_required
@jwt_required
def tournamentRoom(request):
    tournaments = Tournament.objects.all()
    
    for tournament in tournaments:
        tournament.is_user_participant = tournament.is_user_participant(request.user)
    
    return render(request, 'pages/tRoom.html', {'tournaments': tournaments, 'user': request.user})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MatchHistory
from django.contrib.auth import get_user_model

# Varsayılan User modelini alın
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
            'tWinner': match.tWinner  # Bu alanı doğru bir şekilde aktarıyoruz
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
