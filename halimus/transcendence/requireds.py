from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.shortcuts import redirect
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken

def refresh_access_token(refresh_token):
    try:
        # Refresh token'ı doğrula
        refresh = RefreshToken(refresh_token)
        # Yeni access token oluştur
        new_access_token = str(refresh.access_token)
        return new_access_token
    except Exception as e:
        raise Exception('Refresh token doğrulama hatası: ' + str(e))

def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # JWT token'ı cookie'den al
        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik token.'}, status=401)
        
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(raw_token)
            request.user = auth.get_user(validated_token)
        except InvalidToken:
            # Eğer token süresi dolmuşsa, refresh token ile yenileme işlemi yapılabilir
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    new_access_token = refresh_access_token(refresh_token)
                    response = JsonResponse({
                        'success': True,
                        'message': 'Token süresi dolmuş, yeni access token alındı.',
                        'access_token': refresh_token,
                        'refresh_token': refresh_token
                    })
                    response.set_cookie('access_token', new_access_token, httponly=True, secure=True, samesite='Lax')
                    response.set_cookie('refresh_token',refresh_token, httponly=True, secure=True, samesite='Lax')
                    print(f'acces token {new_access_token} \nrefresh token {refresh_token}')
                    # return response
                except Exception as e:
                    return JsonResponse({'success': False, 'message': 'Geçersiz refresh token.'}, status=401)
            else:
                return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik token.'}, status=401)
        
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def notlogin_required(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('user')
        return view_function(request, *args, **kwargs)
    return wrapper_function
