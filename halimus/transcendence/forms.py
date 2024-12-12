from django import forms
from .models import User
from django.core.validators import EmailValidator

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nick', 'email'] # ,'password'
    
    def clean_nick(self):
        nick = self.cleaned_data.get('nick')
        if nick and User.objects.filter(nick=nick).exists():
            raise forms.ValidationError('Bu nick zaten kullanılıyor.')
        return nick

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validator = EmailValidator()

        try:
            validator(email)
        except forms.ValidationError:
            raise forms.ValidationError("Geçersiz e-posta adresi formatı.")
    
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta zaten kullanılıyor.')
        return email
    
    # def clean_password(self):
    #     password = self.cleaned_data.get('password')
    #     if len(password) < 8:
    #         raise forms.ValidationError('şifre en az 8 karakter olmalı.')
    #     if not any(char.isupper() for char in password):
    #         raise forms.ValidationError('Şifre en az bir büyük karakter içermelidir.')
    #     if not any(char.islower() for char in password):
    #         raise forms.ValidationError('Şifre en az bir küçük karakter içermelidir.')
    #     if not any(char in '!@#$%^&*()_+-=[{]}|;:",.<>?/`~' for char in password):
    #         raise forms.ValidationError('Şifre en az bir özel karakter içermelidir.')
    #     return password
# class BlockForm(forms.ModelForm):
#     class Meta:
#         model = Block
#         fields = ['blocker', 'blocked']

#     def clean(self):
#         cleaned_data = super().clean()
#         blocker = cleaned_data.get('blocker')
#         blocked = cleaned_data.get('blocked')

#         # Aynı kullanıcıyı birden fazla engellemek
#         if Block.objects.filter(blocker=blocker, blocked=blocked).exists():
#             raise forms.ValidationError("Bu kullanıcı zaten engellenmiş.")

#         return cleaned_data

# class FriendshipForm(forms.ModelForm):
#     class Meta:
#         model = Friendship
#         fields = ['user', 'friend']

#     def clean(self):
#         cleaned_data = super().clean()
#         user = cleaned_data.get('user')
#         friend = cleaned_data.get('friend')

#         # Aynı kullanıcıya iki kez arkadaşlık teklifi göndermemek
#         if Friendship.objects.filter(user=user, friend=friend).exists():
#             raise forms.ValidationError("Bu kullanıcıyla zaten arkadaşsınız.")

#         return cleaned_data