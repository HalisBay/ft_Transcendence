from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest,JsonResponse,HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout,get_user_model,update_session_auth_hash
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken,UntypedToken
from django.urls import reverse 
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer,LoginSerializer
from datetime import datetime, timedelta
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from .requireds import jwt_required,notlogin_required
import hashlib
import os
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)
User = get_user_model() #TODO:merkezi yapıda kullanmak için bi dosya vs olabilir.




def anonymize_email(email):
    """Emaili anonimleştirmek için hash ve salt kullanılır"""
    salt = os.urandom(16)  # 16 baytlık rastgele tuz oluşturur
    email_salt = salt + email.encode('utf-8')
    return hashlib.sha256(email_salt).hexdigest()

def anonymize_nick(nick):
    """Kullanıcı adını anonimleştirmek için rastgele bir değer ekler"""
    return get_random_string(length=10)

def anonymize_user_data(user):
    """Kullanıcı bilgilerini anonimleştirir"""
    user.email = anonymize_email(user.email)
    user.nick = anonymize_nick(user.nick)
    user.save()

@login_required
def anonymize_account(request):
    user = request.user

    if request.method == 'POST':
        # Kullanıcı bilgilerini anonimleştir
        anonymize_user_data(user)
        messages.success(request, "Hesap bilgileri anonimleştirildi.")
        return redirect('user')  # Kullanıcı bilgileri sayfasına yönlendir
        
    return render(request, 'pages/anonymize_account.html')


def gdpr_page(request):
    return render(request, 'pages/gdpr.html',status = status.HTTP_200_OK)




def index_page(request):
    logger.debug(request)
    return render(request, 'pages/base.html',status = status.HTTP_200_OK)

@notlogin_required
def home_page(request):
    return render(request, 'pages/home.html',status = status.HTTP_200_OK)

@login_required
@jwt_required
def user_page(request):
    user = request.user
    context = {
        'username': user.nick,
        'email': user.email,
    }
    return render(request, 'pages/userInterface.html',context)

def logout_page(request):
    logout(request)
    return redirect('login') 

@api_view(['GET', 'POST'])
def register_user(request):
    if request.method == 'POST':
        serializers = UserSerializer(data = request.data)
        print(serializers)
        if serializers.is_valid():
            serializers.save()
            response_data = {
                "success": True,
                "data": serializers.data,
            }
            messages.success(request, "Kayıt başarılı! Giriş yapabilirsiniz.")
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            print(serializers.errors)
            return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        return render(request, 'pages/signUp.html',status = status.HTTP_200_OK)



@api_view(['GET', 'POST'])
def login_user(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            nick = serializer.validated_data['nick']
            password = serializer.validated_data['password']
            user = authenticate(request, username=nick, password=password)
            if user:
                if user.is_2fa_active:
                    send_verification_email(user)
                    return Response({'success': True, 'message': '2FA doğrulaması gerekiyor. Lütfen e-postanızı kontrol edin.'})
                else:
                    return perform_login(request, user)
            else:
                return Response({'success': False, 'message': 'Geçersiz kullanıcı adı veya şifre.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        return render(request, 'pages/logIn.html',status = status.HTTP_200_OK)


def perform_login(request, user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    login(request, user)
    
    messages.success(request, "Giriş başarılı!") # registerdeki düzgün çalışıyor buradaki bozuk çalışıyor messages.success

    response = redirect('user')
    if not user.is_2fa_active:
        response = Response({
                        'success': False,
                        'message': 'Giriş başarılı!',
                    })
    response.set_cookie(
        'access_token', access_token, httponly=True, secure=True, samesite='Lax'
    )
    print(f"Debug mesaji", {user})
    return response



@api_view(['GET'])
def activate_user(request):
    token = request.GET.get('token')

    try:
        decoded_token = AccessToken(token)
        user_id = decoded_token['user_id']
        user = User.objects.get(id=user_id)
        user.is_active = True 
        user.save()

        return Response({'success': True, 'message': 'Email başarıyla doğrulandı!'}, status=200)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)
    
def generate_activation_token(user):
    refresh = RefreshToken.for_user(user)
    token = refresh.access_token
    token.set_exp(lifetime=timedelta(minutes=5))  # Token süresi 10 dakika
    return str(token)

def send_verification_email(user):
    token = generate_activation_token(user)
    activation_url = f'http://localhost:8000/verify?token={token}'

    subject = 'Email Verification'
    message = f'Please verify your email by clicking the following link: {activation_url}'
    host_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, host_email, [user.email])

def verify_page(request):
    token = request.GET.get('token')
    if token:
        return verify_token(request)
    return render(request, 'pages/verify.html')

@api_view(['GET'])
def verify_token(request):
    token = request.GET.get('token')
    if not token:
        return Response({'success': False, 'message': 'Token bulunamadı.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        decoded_token = UntypedToken(token)
        user_id = decoded_token['user_id']
        user = User.objects.get(id=user_id)
        return perform_login(request, user)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return Response({'success': False, 'message': 'Geçersiz veya süresi dolmuş token.'}, status=status.HTTP_400_BAD_REQUEST)

def verify_fail(request):
    return render(request, 'pages/notverified.html', status=200) #TODO: burası 401 olunca patıyor bakılcak

def activate_2fa(request):
    user = request.user
    if request.method == 'POST':
        if user.is_2fa_active:
            user.is_2fa_active = False
        else:
            user.is_2fa_active = True
        user.save()
        print(user)
        print(user.is_2fa_active)
        return JsonResponse({"success": True, "message": "2FA başarıyla etkinleştirildi."})
    return JsonResponse({"success": False, "message": "Geçersiz istek."}, status=400)


@login_required
@jwt_required
def update(request):
    return render(request, 'pages/update.html', status=200)

@api_view(['POST'])
@jwt_required
def update_nick(request):
    user = request.user
    if user.is_anonymous:
        return Response({'error': 'Kimlik doğrulama başarısız.'}, status=401)

    nick = request.POST.get('nick')
    if not nick:
        messages.error(request, "Kullanıcı adı boş olamaz.")
        return redirect('update')


    serializer = UserSerializer(user, data={'nick': nick}, partial=True)
    if serializer.is_valid():
        serializer.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Kullanıcı adı başarıyla güncellendi.")
        return redirect('user')
    else:
        print(serializer.errors)
        messages.error(request, serializer.errors.get('nick', ["Bir hata oluştu."])[0])

    return redirect('update')

@api_view(['POST'])
@jwt_required
def update_email(request):
    user = request.user
    if user.is_anonymous:
        return Response({'error': 'Kimlik doğrulama başarısız.'}, status=401)
    
    email = request.POST.get('email')
    if not email:
        messages.error(request, "E-posta boş olamaz.")
        return redirect('update')

    serializer = UserSerializer(user, data={'email': email}, partial=True)
    if serializer.is_valid():
        serializer.save()
        update_session_auth_hash(request, user)
        messages.success(request, "E-posta başarıyla güncellendi.")
        return redirect('user')
    else:
        messages.error(request, serializer.errors.get('email', ["Bir hata oluştu."])[0])
    return redirect('update')

@api_view(['POST'])
@jwt_required
def update_password(request):
    user = request.user
    if user.is_anonymous:
        return Response({'error': 'Kimlik doğrulama başarısız.'}, status=401)
    
    new_password = request.POST.get('new_password')
    new_password_confirm = request.POST.get('new_password_confirm')
    if not new_password or not new_password_confirm:
        messages.error(request, "Şifre alanları boş olamaz.")
        return redirect('update')

    if new_password != new_password_confirm:
        messages.error(request, "Şifreler eşleşmiyor.")
        return redirect('update')

    serializer = UserSerializer(user, data={'password': new_password}, partial=True)
    if serializer.is_valid():
        serializer.save()
        messages.success(request, "Şifre başarıyla güncellendi.")
        logout(request)
        return redirect('login')
    else:
        print(serializer.errors)
        messages.error(request, serializer.errors.get('password', ["Bir hata oluştu."])[0])
    return redirect('update')



@login_required
@jwt_required
def delete_all(request):
    if request.method == "POST":
        input_text = request.POST.get("txt", "").strip().lower()  # Gelen metni al ve küçük harfe çevir
        if input_text == "hesabımı sil":
            user = request.user
            if user.is_anonymous:
                return Response({'error': 'Kimlik doğrulama başarısız.'}, status=401)
            user.delete() 
            messages.success(request, "Hesabınız başarıyla silindi.")
            return redirect("home")
        else:
            messages.error(request, "Yanlış metin girdiniz. Lütfen 'hesabımı sil' yazın.")
            return render(request, 'pages/deleteall.html')
    return render(request, 'pages/deleteall.html')
