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
from django.urls import reverse 
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer,LoginSerializer
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model() # merkezi yapıda kullanmak için bi dosya vs olabilir.

def index_page(request):
    logger.debug(request)
    return render(request, 'pages/base.html',status = status.HTTP_200_OK)

def home_page(request):
    return render(request, 'pages/home.html',status = status.HTTP_200_OK)

@login_required
def user_page(request):
    return render(request, 'pages/userInterface.html',status = status.HTTP_200_OK)

def logout_page(request):
    logout(request)  # Kullanıcının oturumunu sonlandırır
    return redirect('login') 

@api_view(['GET', 'POST'])
def register_user(request):
    if request.method == 'POST':
        serializers = UserSerializer(data = request.data)
        print(serializers)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, status=status.HTTP_201_CREATED)
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
            if user is not None:
                login(request, user)
                #send_verification_email(user)
                return Response({'success': True, 'message': 'Giriş başarılı!'}, status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'message': 'Geçersiz kullanıcı adı veya şifre.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        return render(request, 'pages/logIn.html',status = status.HTTP_200_OK)

@api_view(['GET'])
def activate_user(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login',status = status.HTTP_200_OK)
    else:
        return Response({'success': False, 'message': 'Aktivasyon başarısız.'}, status=status.HTTP_400_BAD_REQUEST)

def send_verification_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(str(user.id).encode())
    activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
    activation_url = f'http://localhost:8000{activation_link}'

    subject = 'Email Verification'
    message = f'Please verify your email by clicking the following link: {activation_url}'
    host_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, host_email, [user.email])
