from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserForm
from .forms import LoginForm 
from .models import User
import time

def index_page(request):
    return render(request, 'pages/index.html')

def home_page(request):
    return render(request, 'pages/home.html')

def register_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kayıt başarılı!')
            return redirect('login')
        else:

            messages.error(request, 'Lütfen formdaki hataları düzeltin.')
            return render(request, 'pages/register.html', {'form': form})
    
    return render(request,'pages/register.html')

    
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
    return render(request, 'pages/login.html', {'form': form})