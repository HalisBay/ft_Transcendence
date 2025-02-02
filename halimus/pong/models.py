from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_history')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opponent_history')
    result = models.BooleanField()  # Kazandı mı? (True: kazandı, False: kaybetti)
    win_count = models.IntegerField(default=0)  # Kazandığı oyun sayısı
    lose_count = models.IntegerField(default=0)  # Kaybettiği oyun sayısı
    score = models.IntegerField()  # Skor
    date_time = models.DateTimeField(auto_now_add=True)  # Tarih ve saat
    tWinner = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.user.nick} - {'Kazandı' if self.result else 'Kaybetti'} vs {self.opponent.nick}"

from django.db import models

class Tournament(models.Model):
    creator_alias = models.CharField(max_length=100)
    tournament_name = models.CharField(max_length=100)
    players = models.JSONField(default=list)  # Katılımcıları tutmak için

    def __str__(self):
        return self.tournament_name