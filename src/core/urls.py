from django.urls import path

from mass_validator.views import (
    CheckSiretView,
    CreateResultView,
    LogMeIn,
    UpdateResultView,
    ValidateCreationFileView,
    ValidateUpdateFileView,
)

urlpatterns = [
    path("", ValidateCreationFileView.as_view(), name="home"),
    path(
        "validate-update/",
        ValidateUpdateFileView.as_view(),
        name="validate_update_file",
    ),
    path("create-result", CreateResultView.as_view(), name="create_result"),
    path("result/<str:task_id>/", CreateResultView.as_view(), name="pollable_result"),
    path("siret-result/<str:task_id>/", CheckSiretView.as_view(), name="sirets_result"),
    path("update-result", UpdateResultView.as_view(), name="update_result"),
    path("log-me-in", LogMeIn.as_view(), name="log_me_in"),
]
