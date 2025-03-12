from django.db import models
import os
import shutil

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, nick, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Kullanıcıların bir e-posta adresi olmalı")
        email = self.normalize_email(email)
        user = self.model(nick=nick, email=email, **extra_fields)
        return user

class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    nick = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, default="Kolaydegildir123.")
    avatar = models.ImageField(upload_to='avatars/', default='user1.jpg', blank=True, null=True)
    is_online = models.BooleanField(default=False)
    is_anonymized = models.BooleanField(default=False)
    alias = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True)#default false olarak ayarlanacak kullanıcı login olurken true olucak
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # Varsayılan olarak şimdiye ayarlanır
    is_2fa_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'nick'
    REQUIRED_FIELDS = ['email']  # Süper kullanıcı oluşturulurken gerekli alanlar

    def __str__(self):
        return self.nick



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




# class MatchHistory(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_history')
#     result = models.BooleanField()  # Kazandı mı? (True: kazandı, False: kaybetti)
#     win_rate = models.FloatField()  # Kazanma oranı
#     score = models.IntegerField()  # Skor
#     opponent = models.CharField(max_length=50)  # Rakip oyuncu (nick veya ID)
#     date_time = models.DateTimeField(auto_now_add=True)  # Tarih ve saat

#     def __str__(self):
#         return f"{self.user.nick} - {'Kazandı' if self.result else 'Kaybetti'}"
