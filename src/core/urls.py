from django.urls import path

from mass_validator.views import CheckSiretView, ResultView, ValidateView

urlpatterns = [
    path("", ValidateView.as_view(), name="home"),
    path("result", ResultView.as_view(), name="result"),
    path("result/<str:task_id>/", ResultView.as_view(), name="pollable_result"),
    path("siret-result/<str:task_id>/", CheckSiretView.as_view(), name="sirets_result"),
]
