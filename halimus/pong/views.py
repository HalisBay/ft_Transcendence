from django.shortcuts import render
from transcendence.requireds import jwt_required
from django.contrib.auth.decorators import login_required
@login_required
@jwt_required
def pong(request):
    return render(request, 'pages/index2.html')

@login_required
@jwt_required
def gameHome(request):
    return render(request, 'pages/gameHome.html')

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import MatchHistory

User = get_user_model()

def profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    match_history = MatchHistory.objects.filter(user=user).order_by('-date_time')
    context = {
        'profile_user': user,
        'match_history': match_history
    }
    return render(request, 'pages/profile.html', context)
