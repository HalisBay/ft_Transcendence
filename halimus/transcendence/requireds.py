from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
# from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


def jwt_required(view_func):
    """
    Custom decorator for checking the validity of JWT in requests.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # JWT token'ı header'dan alıyoruz
        token = request.COOKIES.get('access_token')
        
        if not token:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik token.'}, status=401)
        
        try:
            # JWT token doğrulaması
            JWTAuthentication().authenticate(request)
        except AuthenticationFailed:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik token.'}, status=401)
        
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def notlogin_required(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('user')  # Giriş yapmış kullanıcıları yönlendireceğiniz sayfa
        return view_function(request, *args, **kwargs)
    return wrapper_function