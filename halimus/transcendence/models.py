from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, nick, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Kullanıcıların bir e-posta adresi olmalı")
        email = self.normalize_email(email)
        user = self.model(nick=nick, email=email, **extra_fields)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    nick = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, default="Kolaydegildir123.")
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # Varsayılan olarak şimdiye ayarlanır

    objects = UserManager()

    USERNAME_FIELD = 'nick'
    REQUIRED_FIELDS = ['email']  # Süper kullanıcı oluşturulurken gerekli alanlar

    def __str__(self):
        return self.nick




# class MatchHistory(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_history')
#     result = models.BooleanField()  # Kazandı mı? (True: kazandı, False: kaybetti)
#     win_rate = models.FloatField()  # Kazanma oranı
#     score = models.IntegerField()  # Skor
#     opponent = models.CharField(max_length=50)  # Rakip oyuncu (nick veya ID)
#     date_time = models.DateTimeField(auto_now_add=True)  # Tarih ve saat

#     def __str__(self):
#         return f"{self.user.nick} - {'Kazandı' if self.result else 'Kaybetti'}"

# class Block(models.Model):
#     blocker = models.ForeignKey(User, related_name="blocker", on_delete=models.CASCADE)
#     blocked = models.ForeignKey(User, related_name="blocked", on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     def __str__(self):
#         return f"{self.user.nick} - {self.blocked_users.count()} kullanıcı engelledi"

# class FriendList(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='friend_list')
#     friends = models.ManyToManyField(User, related_name='friend_of')

#     def __str__(self):
#         return f"{self.user.nick} - {self.friends.count()} arkadaş"

