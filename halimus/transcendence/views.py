from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user_model,
    update_session_auth_hash,
)
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, UntypedToken
from django.urls import reverse
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer
from datetime import datetime, timedelta
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from .requireds import jwt_required, notlogin_required
from django.core.files.storage import default_storage
from .models import copy_static_to_media
from django.core.files.base import ContentFile
from functools import wraps
import hashlib
import os
from django.utils.crypto import get_random_string
from django.core.files.storage import FileSystemStorage
from mimetypes import guess_type
from halimus.settings import host_ip
from django.views.decorators.csrf import csrf_protect


logger = logging.getLogger(__name__)
User = get_user_model()  # TODO:merkezi yapıda kullanmak için bi dosya vs olabilir.


def anonymize_email(email):
    """Emaili anonimleştirmek için hash ve salt kullanılır"""
    salt = os.urandom(16)  # 16 baytlık rastgele tuz oluşturur
    email_salt = salt + email.encode("utf-8")
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
@jwt_required
def anonymize_account(request):
    user = request.user

    if request.method == "POST":
        # Kullanıcı bilgilerini anonimleştir
        anonymize_user_data(user)
        messages.success(request, "Hesap bilgileri anonimleştirildi.")
        return JsonResponse({"success": True}, status=200)

    return render(request, "pages/anonymize_account.html")


def about_page(request):
    return render(request, "pages/about.html", status=status.HTTP_200_OK)


def gdpr_page(request):
    return render(request, "pages/gdpr.html", status=status.HTTP_200_OK)


def index_page(request):
    logger.debug(request)
    return render(request, "pages/base.html", status=status.HTTP_200_OK)


@notlogin_required
def home_page(request):
    return render(request, "pages/home.html", status=status.HTTP_200_OK)


@login_required
@jwt_required
def user_page(request):
    user = request.user
    context = {
        "username": user.nick,
        "email": user.email,
    }
    return render(request, "pages/userInterface.html", context)


from rest_framework_simplejwt.tokens import RefreshToken

from django.http import JsonResponse
from django.shortcuts import render


@csrf_protect
@api_view(["POST"])
@jwt_required
def logout_page(request):
    if request.user.is_authenticated:
        user = request.user
        user.is_online = False
        user.save()

    print(f"\nuser online {request.user.is_online}\n")
    # Django oturumunu sonlandır
    logout(request)

    # Çerezleri temizle
    response = JsonResponse({"success": True, "message": "Çıkış yapılıyor."})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrftoken")

    # Önbelleği temizle
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


@notlogin_required
@api_view(["GET", "POST"])
def register_user(request):
    if request.method == "POST":
        serializers = UserSerializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response(
                {"success": True, "message": "Kayıt başarılı."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "errors": serializers.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "GET":
        return render(request, "pages/signUp.html", status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def login_user(request):
    copy_static_to_media()
    if request.method == "POST":
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            nick = serializer.validated_data["nick"]
            password = serializer.validated_data["password"]
            user = authenticate(request, username=nick, password=password)
            if user:
                if not user.is_online:
                    user.is_online = True
                    user.save()

                if user.is_2fa_active:
                    send_verification_email(user)
                    return Response(
                        {
                            "success": True,
                            "message": "2FA doğrulaması gerekiyor. Lütfen e-postanızı kontrol edin.",
                        }
                    )
                else:
                    return perform_login(request, user)
            else:
                return Response(
                    {
                        "success": False,
                        "message": "Geçersiz kullanıcı adı veya şifre.2",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif request.method == "GET":
        return render(request, "pages/logIn.html", status=status.HTTP_200_OK)


def perform_login(request, user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    login(request, user)

    response = redirect("user")
    if not user.is_2fa_active:
        response = Response(
            {
                "success": True,
                "message": "Giriş başarılı!",
            }
        )
    response.set_cookie(
        "access_token", access_token, httponly=True, samesite="Lax", secure=True
    )
    response.set_cookie(
        "refresh_token", refresh_token, httponly=True, samesite="Lax", secure=True
    )
    print(f"Debug mesaji", {user})
    return response


@api_view(["GET"])
def activate_user(request):
    token = request.GET.get("token")

    try:
        decoded_token = AccessToken(token)
        user_id = decoded_token["user_id"]
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

        return Response(
            {"success": True, "message": "Email başarıyla doğrulandı!"}, status=200
        )
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)


def generate_activation_token(user):
    refresh = RefreshToken.for_user(user)
    token = refresh.access_token
    token.set_exp(lifetime=timedelta(minutes=2))  # Token süresi 10 dakika
    return str(token)


def send_verification_email(user):
    token = generate_activation_token(user)
    activation_url = f"https://{host_ip}:8001/verify?token={token}"

    subject = "Email Verification"
    message = (
        f"Please verify your email by clicking the following link: {activation_url}"
    )
    host_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, host_email, [user.email])


def verify_page(request):
    token = request.GET.get("token")
    if token:
        return verify_token(request)
    return render(request, "pages/verify.html")


@api_view(["GET"])
def verify_token(request):
    token = request.GET.get("token")
    if not token:
        return Response(
            {"success": False, "message": "Token bulunamadı."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        decoded_token = UntypedToken(token)
        user_id = decoded_token["user_id"]
        user = User.objects.get(id=user_id)
        return perform_login(request, user)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return Response(
            {"success": False, "message": "Geçersiz veya süresi dolmuş token."},
            status=status.HTTP_400_BAD_REQUEST,
        )


def verify_fail(request):
    return render(
        request, "pages/notverified.html", status=200
    )  # TODO: burası 401 olunca patıyor bakılcak


def activate_2fa(request):
    user = request.user
    if request.method == "POST":
        if user.is_2fa_active:
            user.is_2fa_active = False
        else:
            user.is_2fa_active = True
        user.save()
        print(user)
        print(user.is_2fa_active)
        return JsonResponse(
            {"success": True, "message": "2FA başarıyla etkinleştirildi."}
        )
    return JsonResponse({"success": False, "message": "Geçersiz istek."}, status=400)


@login_required
@jwt_required
def update(request):
    return render(request, "pages/update.html", status=200)


def format_messages(messages):
    return "<br>".join(messages)


@api_view(["POST"])
@jwt_required
@login_required
def update_user(request):
    user = request.user
    if user.is_anonymous:
        return Response({"error": "Kimlik doğrulama başarısız."}, status=401)

    # Güncellenecek alanları al
    nick = request.POST.get("nick")
    email = request.POST.get("email")
    new_password = request.POST.get("new_password")
    new_password_confirm = request.POST.get("new_password_confirm")
    selected_avatar = request.POST.get("select_avatar")
    avatar_file = request.FILES.get("avatar_file")

    messages = []

    # Kullanıcı adı güncelleme
    if nick:
        serializer = UserSerializer(user, data={"nick": nick}, partial=True)
        if serializer.is_valid():
            serializer.save()
            update_session_auth_hash(request, user)
            messages.append("Kullanıcı adı başarıyla güncellendi.")
        else:
            messages.append(
                serializer.errors.get("nick", ["Kullanıcı adı güncellenemedi."])[0]
            )

    # E-posta güncelleme
    if email:
        serializer = UserSerializer(user, data={"email": email}, partial=True)
        if serializer.is_valid():
            serializer.save()
            update_session_auth_hash(request, user)
            messages.append("E-posta başarıyla güncellendi.")
        else:
            messages.append(
                serializer.errors.get("email", ["E-posta güncellenemedi."])[0]
            )

    # Şifre güncelleme
    if new_password and new_password_confirm:
        if new_password != new_password_confirm:
            messages.append("Şifreler eşleşmiyor.")
        else:
            serializer = UserSerializer(
                user, data={"password": new_password}, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                messages.append("Şifre başarıyla güncellendi, Çıkış yapılıyor.")
                logout(request)
            else:
                messages.append(
                    serializer.errors.get("password", ["Şifre güncellenemedi."])[0]
                )

    # Avatar güncelleme
    if avatar_file:
        # İzin verilen MIME türleri
        allowed_mime_types = ["image/jpeg", "image/png", "image/gif"]

        # MIME türünü belirleme
        mime_type, _ = guess_type(avatar_file.name)

        if mime_type not in allowed_mime_types:
            messages.append("Yalnızca JPEG, PNG veya GIF dosyaları yükleyebilirsiniz.")
        else:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "avatars")
            )
            filename = fs.save(avatar_file.name, avatar_file)
            request.user.avatar = os.path.join("avatars", filename)
            request.user.save()
            messages.append("Avatar başarıyla yüklendi ve güncellendi.")

    elif selected_avatar:
        user.avatar = selected_avatar
        user.save()
        messages.append("Avatar başarıyla güncellendi.")

    formatted_messages = format_messages(messages)
    return JsonResponse({"success": True, "message": formatted_messages}, status=200)


def get_avatar_list():
    avatar_dir = os.path.join(settings.MEDIA_ROOT, "avatars")
    avatars = [
        f for f in os.listdir(avatar_dir) if os.path.isfile(os.path.join(avatar_dir, f))
    ]
    return avatars


def profile_edit_view(request):
    avatars = get_avatar_list()
    context = {
        "avatars": avatars,
    }
    return render(request, "pages/userInterface.html", context)


@login_required
@jwt_required
def delete_all(request):
    if request.method == "POST":
        input_text = (
            request.POST.get("txt", "").strip().lower()
        )  # Gelen metni al ve küçük harfe çevir
        if input_text == "hesabımı sil":
            user = request.user
            if user.is_anonymous:
                return Response({"error": "Kimlik doğrulama başarısız."}, status=401)
            user.delete()
            return redirect("home")
        else:
            return render(request, "pages/deleteall.html")
    return render(request, "pages/deleteall.html")
