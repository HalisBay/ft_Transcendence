from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

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
            return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik token.'}, status=401)
        
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def notlogin_required(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('user')
        return view_function(request, *args, **kwargs)
    return wrapper_function
