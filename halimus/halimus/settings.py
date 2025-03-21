"""
Django settings for halimus project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import environ
import os
import socket

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "transcendence",
    "django.contrib.sites",
    #'debug_toolbar',
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "pong",
    "friends",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    #'debug_toolbar.middleware.DebugToolbarMiddleware'
]

ROOT_URLCONF = "halimus.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["/usr/share/nginx/static", BASE_DIR / "/static/"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "halimus.wsgi.application"
ASGI_APPLICATION = "halimus.asgi.application"


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6380)],
        },
    },
}
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

LOGIN_REDIRECT_URL = "/home"

APPEND_SLASH = False

env = environ.Env()
environ.Env.read_env(BASE_DIR / "docker" / ".env")

DATABASES = {"default": env.db("DATABASE_URL")}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
ALLOWED_HOSTS.append(env("HOSTIP", default="127.0.0.1"))

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

AUTH_USER_MODEL = "transcendence.User"

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "/static"


MEDIA_URL = "/media/"
MEDIA_ROOT = "/usr/share/nginx/media/"


# if DEBUG:
STATICFILES_DIRS = ["/usr/share/nginx/static/"]
# Front-end statik dosyalarının yolu


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

host_ip = env("HOSTIP", default="127.0.0.1")  # Varsayılan IP'yi veriyoruz

print(host_ip)
CSRF_TRUSTED_ORIGINS = [f"https://{host_ip}:8001", "https://localhost:8001"]


# annotations
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/user"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
from datetime import datetime, timedelta


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),  # Access token'ın süresi
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=2),  # Refresh token'ın süresi
    "ROTATE_REFRESH_TOKENS": True,  # Refresh token'ı döndürme özelliği
    "BLACKLIST_AFTER_ROTATION": True,  # Eski refresh token'ları geçersiz kıl
}

# Security settings
SECURE_SSL_REDIRECT = True  # Tüm HTTP isteklerini HTTPS'ye yönlendirir
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # Nginx tarafından iletilen başlıkları kontrol eder
CSRF_COOKIE_SECURE = True  # CSRF çerezlerini sadece HTTPS üzerinden gönderir
SESSION_COOKIE_SECURE = True  # Oturum çerezlerini sadece HTTPS üzerinden gönderir
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SITE_ID = 1
