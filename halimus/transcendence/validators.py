# from django.core.exceptions import ValidationError

# class SpecialCharacterValidator:
#     def __call__(self, password, user=None):
#         if not any(char in '!@#$%^&*()_+-=[{]}|;:",.<>?/`~' for char in password):
#             raise ValidationError('Şifre en az bir özel karakter içermeli.')

#     def get_help_text(self):
#         return 'Şifrenizde en az bir özel karakter (!, @, #, $, vb.) bulunmalıdır.'

# class UppercaseValidator:
#     def __call__(self, password, user=None):
#         if not any(char.isupper() for char in password):
#             raise ValidationError('Şifre en az bir büyük harf içermeli.')

#     def get_help_text(self):
#         return 'Şifrenizde en az bir büyük harf bulunmalıdır.'
