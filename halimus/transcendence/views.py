from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate,login,logout
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse 
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer,LoginSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from functools import wraps
from .requireds import jwt_required,notlogin_required
logger = logging.getLogger(__name__)
User = get_user_model() #TODO:merkezi yapıda kullanmak için bi dosya vs olabilir.



def index_page(request):
    logger.debug(request)
    return render(request, 'pages/base.html',status = status.HTTP_200_OK)

@notlogin_required
def home_page(request):
    return render(request, 'pages/home.html',status = status.HTTP_200_OK)

@login_required
@jwt_required
def user_page(request):
    return render(request, 'pages/userInterface.html',status = status.HTTP_200_OK)

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
            if user:#alinin butonu ve model ayarlancak
                if True:
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
    
    messages.success(request, "Giriş başarılı!")
    
    response = redirect('user')
    response.set_cookie(
        'access_token', access_token, httponly=True, secure=True, samesite='Lax'
    )
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
    token = refresh.access_token  # Aktivasyon için sadece access token kullanılır
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
