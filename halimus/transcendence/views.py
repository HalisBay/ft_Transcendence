from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login
from .forms import UserForm
from .forms import LoginForm 
from .models import User

def index_page(request):
    return render(request, 'pages/index.html')

def home_page(request):
    return render(request, 'pages/home.html')

def register_user(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})  # Başarı durumunda JSON dönüyoruz
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': errors})  # Hataları döndürüyoruz

    # Eğer gelen istek AJAX değilse, normal sayfa render ediliyor
    form = UserForm()
    return render(request, 'pages/signUp.html', {'form': form})

    
def login_page(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nick = form.cleaned_data.get('nick')
            password = form.cleaned_data.get('password')
            messages.success(request, 'Samet başarılı!')
            return redirect('home')
        else:
            messages.error(request, 'Lütfen formdaki hataları düzeltin.')
    else:
        form = LoginForm()
    return render(request, 'pages/logIn.html', {'form': form})