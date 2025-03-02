from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .models import User
from django.core.validators import EmailValidator
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["nick", "email", "password"]

    def validate_nick(self, value):
        if User.objects.filter(nick=value).exists():
            raise serializers.ValidationError("Bu nick zaten kullanılıyor.")

        return value

    def validate_email(self, value):
        # Email formatı doğrulama
        try:
            EmailValidator()(value)
        except ValidationError:
            raise serializers.ValidationError("Geçersiz e-posta adresi formatı.")

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu e-posta zaten kullanılıyor.")
        return value

    def validate_password(self, value):
        # Şifre doğrulama
        if len(value) < 8:
            raise serializers.ValidationError("Şifre en az 8 karakter olmalı.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Şifre en az bir büyük karakter içermelidir."
            )
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Şifre en az bir küçük karakter içermelidir."
            )
        if not any(char in '!@#$%^&*()_+-=[{]}|;:",.<>?/`~' for char in value):
            raise serializers.ValidationError(
                "Şifre en az bir özel karakter içermelidir."
            )
        return value

    def create(self, validated_data):
        # Şifreyi şifrele ve kullanıcıyı oluştur
        validated_data["password"] = make_password(validated_data["password"])
        user = User.objects.create(**validated_data)
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "password" and value:
                value = make_password(value)
            setattr(instance, attr, value)  # Diğer alanları güncelle
        instance.save()  # Güncellenmiş örneği kaydet
        return instance


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    nick = serializers.CharField(max_length=150, required=True, label="Kullanıcı Adı")
    password = serializers.CharField(write_only=True, required=True, label="şifre")

    def validate(self, data):
        username = data.get("nick")
        password = data.get("password")

        if username and password:
            try:
                user = User.objects.get(nick=username)
                if not check_password(password, user.password):
                    raise serializers.ValidationError(
                        "Geçersiz kullanıcı adı veya şifre."
                    )
                if user.is_online == True:
                    raise serializers.ValidationError("Oturum zaten açık")
            except User.DoesNotExist:
                raise serializers.ValidationError("Geçersiz kullanıcı adı veya şifre.")
        else:
            raise serializers.ValidationError("Kullanıcı adı ve şifre gereklidir.")

        data["user"] = user
        return data
