from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate,login,logout
from .forms import UserForm
from .forms import LoginForm
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse 
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required


logger = logging.getLogger(__name__)

def index_page(request):
    logger.debug(request)
    return render(request, 'pages/base.html')

def home_page(request):
    return render(request, 'pages/home.html')

@login_required
def user_page(request):
    return render(request, 'pages/userInterface.html')

def logout_page(request):
    logout(request)  # Kullanıcının oturumunu sonlandırır
    return redirect('login') 

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


def activate(request, uidb64, token):
    try:
        # URL'den gelen kullanıcı ID'sini çözümle
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True  # Kullanıcıyı aktif yap
        user.save()
        return redirect('login')  # Kullanıcıyı giriş sayfasına yönlendir
    else:
        return render(request, 'activation_failed.html')  # Doğrulama başarısızsa hata sayfası



def login_page(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nick = form.cleaned_data.get('nick')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=nick, password=password)
            print(f'DEbug msg.: 1{user}')
            if user is not None:
                login(request, user)
                #send_verification_email(user)
                messages.success(request, 'Giriş başarılı!')
                return JsonResponse({'success': True})
            else:
                messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': errors})
    else:
        form = LoginForm()

    return render(request, 'pages/logIn.html', {'form': form})


def send_verification_email(user):
    # Kullanıcıyı ve token'ı oluştur
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(str(user.id).encode())  # Kullanıcı ID'sini encode et
    activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
    activation_url = f'http://localhost:8000{activation_link}'  # Uygulama URL'si

    subject = 'Email Verification'
    message = f'Please verify your email by clicking the following link: {activation_url}'
    host_email = settings.EMAIL_HOST_USER
    # E-posta gönder
    send_mail(subject, message,host_email, [user.email])