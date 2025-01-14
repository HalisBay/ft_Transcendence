from django.shortcuts import render

def pong(request):
    return render(request, 'pages/index2.html')

def gameHome(request):
    return render(request, 'pages/gameHome.html')