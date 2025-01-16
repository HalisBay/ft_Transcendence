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