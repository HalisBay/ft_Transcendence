from django import forms
from .models import User
from django.contrib.auth.hashers import check_password
from django.core.validators import EmailValidator
from django.contrib import messages
from django.contrib.auth.hashers import make_password

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nick', 'email','password']
    
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
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('şifre en az 8 karakter olmalı.')
        if not any(char.isupper() for char in password):
            raise forms.ValidationError('Şifre en az bir büyük karakter içermelidir.')
        if not any(char.islower() for char in password):
            raise forms.ValidationError('Şifre en az bir küçük karakter içermelidir.')
        if not any(char in '!@#$%^&*()_+-=[{]}|;:",.<>?/`~' for char in password):
            raise forms.ValidationError('Şifre en az bir özel karakter içermelidir.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    nick = forms.CharField(max_length=150, required=True, label='Kullanıcı Adı')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Şifre')

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('nick')
        password = cleaned_data.get('password')

        if username and password:
            try:
                user = User.objects.get(nick=username)
                if not check_password(password, user.password) and user:
                   raise forms.ValidationError('Geçersiz kullanıcı adı veya şifre.')
            except User.DoesNotExist:
                raise forms.ValidationError('Geçersiz kullanıcı adı veya şifre.')
        return cleaned_data
        


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