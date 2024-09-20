from django import forms
from django.conf import settings

from .fields import MathCaptchaField


class UploadCreationForm(forms.Form):
    file = forms.FileField(label="Fichier d'import en masse")
    captcha = MathCaptchaField(label="Anti robots")


class UploadUpdateForm(forms.Form):
    file = forms.FileField(label="Fichier de modification en masse")
    captcha = MathCaptchaField(label="Anti robots")


class LogMeInForm(forms.Form):
    name = forms.CharField(label="Identifiant")
    password = forms.CharField(widget=forms.PasswordInput(), label="Mot de passe")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["name"] != settings.USERNAME or cleaned_data["password"] != settings.PASSWORD:
            raise forms.ValidationError("Les identifiants sont incorrects")

        return cleaned_data
