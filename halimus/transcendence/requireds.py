from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.shortcuts import redirect
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout


def refresh_access_token(refresh_token):
    try:
        # Refresh token'ı doğrula
        refresh = RefreshToken(refresh_token)
        # Yeni access token oluştur
        new_access_token = str(refresh.access_token)
        return new_access_token
    except Exception as e:
        raise Exception("Refresh token validation failure: " + str(e))


def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        raw_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        if not raw_token:
            return JsonResponse(
                {"success": False, "message": "Invalid or missing access token."},
                status=401,
            )

        try:
            # Access token'ı doğrula
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(raw_token)
            request.user = auth.get_user(validated_token)
        except InvalidToken:
            if refresh_token:
                try:
                    new_access_token = refresh_access_token(refresh_token)
                    response = JsonResponse(
                        {
                            "success": True,
                            "message": "Token expired, new access token received.",
                        }
                    )
                    response.set_cookie(
                        "access_token",
                        new_access_token,
                        httponly=True,
                        secure=True,
                        samesite="Lax",
                    )

                    # Yeni access token'ı kullanarak doğrulama yap
                    validated_token = JWTAuthentication().get_validated_token(
                        new_access_token
                    )
                    request.user = JWTAuthentication().get_user(validated_token)
                except Exception as e:
                    return JsonResponse(
                        {"success": False, "message": "Invalid refresh token."},
                        status=401,
                    )
            else:
                return JsonResponse(
                    {"success": False, "message": "Invalid or missing refresh token."},
                    status=401,
                )

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def notlogin_required(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("user")
        return view_function(request, *args, **kwargs)

    return wrapper_function

def logout_and_clear_cache(request,message):
    logout(request)

    # Çerezleri temizle
    response = JsonResponse({"success": True, "message": message})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrftoken")

    # Önbelleği temizle
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response