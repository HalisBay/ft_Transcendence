from django.db import models
import os
import shutil

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, nick, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)

        user = self.model(nick=nick, email=email, **extra_fields)

        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nick, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(nick, email, password, **extra_fields)

class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    nick = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, default="Kolaydegildir123.")
    avatar = models.ImageField(upload_to='avatars/', default='user1.jpg', blank=True, null=True)
    is_online = models.BooleanField(default=False)
    is_anonymized = models.BooleanField(default=False)
    alias = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    is_2fa_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'nick'
    REQUIRED_FIELDS = ['email']  # Süper kullanıcı oluşturulurken gerekli alanlar

    def __str__(self):
        return self.nick

    def has_module_perms(self, app_label):
            """
            Kullanıcının, belirtilen uygulama etiketinde (app_label) izinlere sahip olup olmadığını kontrol eder.
            Admin paneli için gerekli.
            """
            return self.is_superuser or self.is_staff

    def has_perm(self, perm, obj=None):
            """
            Kullanıcının belirtilen izinlere sahip olup olmadığını kontrol eder.
            Admin paneli için gerekli.
            """
            return self.is_superuser or self.is_staff

def copy_static_to_media():
    static_path = "/usr/share/nginx/static/assets/images"
    media_path = "/usr/share/nginx/media"

    # Eğer Media dizini yoksa, oluştur
    if not os.path.exists(media_path):
        os.makedirs(media_path)

    # Static dizinindeki tüm dosyaları al
    for filename in os.listdir(static_path):
        # Dosya yolunu oluştur
        file_path = os.path.join(static_path, filename)
        
        # Eğer bu bir dosya ise (klasör değil), kopyala
        if os.path.isfile(file_path):
            shutil.copy(file_path, media_path)
