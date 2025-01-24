from django.db import models
import os
import shutil
from django.conf import settings
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

    anonymized_nick = models.CharField(max_length=50, null=True, blank=True)
    anonymized_email = models.EmailField(null=True, blank=True)

    is_active = models.BooleanField(default=True)#default false olarak ayarlanacak kullanıcı login olurken true olucak
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # Varsayılan olarak şimdiye ayarlanır
    is_2fa_active = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'nick'
    REQUIRED_FIELDS = ['email']  # Süper kullanıcı oluşturulurken gerekli alanlar

    def __str__(self):
        return self.nick

    def anonymize(self):
        """Kullanıcıyı anonimleştirir."""
        self.anonymized_nick = f"anon_{self.id}"
        self.anonymized_email = f"anon_{self.id}@example.com"
        self.nick = self.anonymized_nick
        self.email = self.anonymized_email
        self.save()


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


class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_list")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="friends")

    def __str__(self):
        return f"{self.user.nick}'s friends"

    def add_friend(self, friend):
        self.friends.add(friend)

    def remove_friend(self, friend):
        self.friends.remove(friend)

    def is_friend(self, friend):
        """Arkadaşlık kontrolü"""
        return self.friends.filter(id=friend.id).exists()

class FriendRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_sent"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received"
    )
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.from_user.nick} to {self.to_user.nick} - {self.status}"

    class Meta:
        unique_together = ('from_user', 'to_user')  # Aynı iki kullanıcı arasında birden fazla istek olmasın.

    def accept(self):
        self.status = 'accepted'
        self.save()
        # Kullanıcıları arkadaş listesine ekleme
        FriendList.objects.get_or_create(user=self.from_user)[0].add_friend(self.to_user)
        FriendList.objects.get_or_create(user=self.to_user)[0].add_friend(self.from_user)
        self.delete()

    def reject(self):
        self.status = 'rejected'
        self.save()
        self.delete()

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

