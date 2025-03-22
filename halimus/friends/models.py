from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_list")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="friends")

    def __str__(self):
        return f"Friend list of {self.user.nick or 'Unknown User'}"

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
        from_user_nick = self.from_user.nick or "Unknown"
        to_user_nick = self.to_user.nick or "Unknown"
        return f"{from_user_nick} -> {to_user_nick} ({self.status})"

    class Meta:
        unique_together = ('from_user', 'to_user')  # Aynı iki kullanıcı arasında birden fazla istek olmasın.

    def accept(self):
        self.status = 'accepted'
        self.save()
        FriendList.objects.get_or_create(user=self.from_user)[0].add_friend(self.to_user)
        FriendList.objects.get_or_create(user=self.to_user)[0].add_friend(self.from_user)
        FriendRequest.objects.filter(
            from_user=self.to_user, to_user=self.from_user, status='pending'
        ).delete()
        self.delete()

    def reject(self):
        self.status = 'rejected'
        self.save()
        FriendRequest.objects.filter(
            from_user=self.to_user, to_user=self.from_user, status='pending'
        ).delete()
        self.delete()