from django.db import models
# from .validators import SpecialCharacterValidator, UppercaseValidator

class User(models.Model):
    # id = models.AutoField(primary_key=True)
    # skor = models.IntegerField(default=0)
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    nick = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # Boş değer kabul et
    # password = models.CharField(max_length=128)

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

