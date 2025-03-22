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
        match_type = "Tournament" if self.is_tournament else "Casual"
        result_text = "Winner" if self.result else "Loser"
        return (
            f"{self.user.nick} ({self.score}) vs {self.opponent.nick} ({self.opponent_score}) - "
            f"{result_text} - {match_type} Match"
        )


