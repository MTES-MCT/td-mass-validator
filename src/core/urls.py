from django.urls import path

from mass_validator.views import ResultView, ValidateView

urlpatterns = [
    path("", ValidateView.as_view(), name="home"),
    path("result", ResultView.as_view(), name="result"),
]
