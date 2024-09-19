import pytest
from django.conf import settings

from ..fields import hash_answer

pytestmark = pytest.mark.django_db

OK_FILE = settings.BASE_DIR / "tst_files" / "file_ok.xlsx"


def test_upload_view_get(anon_client):
    res = anon_client.get("/")
    assert res.status_code == 200


def test_upload_view_post(anon_client):
    with open(OK_FILE, "rb") as upload:
        res = anon_client.post(
            "/",
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
            follow=True,
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" not in content
