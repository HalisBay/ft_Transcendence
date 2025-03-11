from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MatchHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="match_history"
    )
    opponent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="opponent_history"
    )
    result = models.BooleanField()  # Kazandı mı? (True: kazandı, False: kaybetti)
    win_count = models.IntegerField(default=0)  # Kazandığı oyun sayısı
    lose_count = models.IntegerField(default=0)  # Kaybettiği oyun sayısı
    score = models.IntegerField()  # Skor
    opponent_score = models.IntegerField(default=0) 
    date_time = models.DateTimeField(auto_now_add=True)  # Tarih ve saat
    tWinner = models.BooleanField(default=False)
    is_tournament = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.nick} - {'Kazandı' if self.result else 'Kaybetti'} vs {self.opponent.nick}"


class Tournament(models.Model):
    tournament_name = models.CharField(max_length=100)
    creator_alias = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def participant_count(self):
        return TournamentParticipant.objects.filter(tournament=self).count()

    def is_user_participant(self, user):
        return TournamentParticipant.objects.filter(tournament=self, user=user).exists()

    def __str__(self):
        return self.name


class TournamentParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Katılımcı oyuncu
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE
    )  # Katıldığı turnuva
    alias = models.CharField(max_length=50)  # Oyuncunun turnuvada kullandığı alias

    def __str__(self):
        return f"{self.alias} in {self.tournament.tournament_name}"
