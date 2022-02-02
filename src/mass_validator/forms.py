from django import forms

from .fields import MathCaptchaField


class UploadForm(forms.Form):
    file = forms.FileField(label="Fichier d'import en masse")

    captcha = MathCaptchaField(label="Anti robots")
