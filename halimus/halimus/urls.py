"""
URL configuration for halimus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.urls import path, re_path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from transcendence.views import spa

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('',include('transcendence.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Giriş için
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh için
    path('game/', include('pong.urls')),
    re_path(r'^.*$', TemplateView.as_view(template_name='pages/404.html'), name='page_not_found'),
]
