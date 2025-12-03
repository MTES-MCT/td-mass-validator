import json
from http.cookies import SimpleCookie

import pytest
from django.conf import settings
from django.core import signing
from django.urls import reverse

from ..fields import hash_answer

pytestmark = pytest.mark.django_db

IMPORT_ETAB_OK = settings.SRC_DIR / "tst_files" / "create_etabs_ok.xlsx"
IMPORT_ETAB_NOT_OK = settings.SRC_DIR / "tst_files" / "create_etabs_not_ok.xlsx"
MODIF_ETAB_OK = settings.SRC_DIR / "tst_files" / "modif_etabs_ok.xlsx"
MODIF_ETAB_NOT_OK = settings.SRC_DIR / "tst_files" / "modif_etabs_not_ok.xlsx"


def test_upload_view_get(anon_client):
    res = anon_client.get("/")
    assert res.status_code == 200


def test_upload_create_view_post(anon_client):
    with open(IMPORT_ETAB_OK, "rb") as upload:
        res = anon_client.post(
            "/",
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
            follow=True,
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" not in content


def test_upload_create_view_post_fail(anon_client):
    with open(IMPORT_ETAB_NOT_OK, "rb") as upload:
        res = anon_client.post(
            "/",
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" in content
    assert "Le champ companyTypes doit contenir COLLECTOR." in content


def test_upload_update_view_post(anon_client):
    with open(MODIF_ETAB_OK, "rb") as upload:
        res = anon_client.post(
            reverse("validate_update_file"),
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
            follow=True,
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" not in content


expected_json_dict = [
    {
        "orgId": "00000000014140",
        "companyTypes": ["WASTEPROCESSOR", "COLLECTOR"],
        "collectorTypes": ["DANGEROUS_WASTES"],
        "wasteProcessorTypes": ["OTHER_DANGEROUS_WASTES", "CREMATION"],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000010189",
        "companyTypes": ["WASTEPROCESSOR", "COLLECTOR"],
        "collectorTypes": ["DANGEROUS_WASTES"],
        "wasteProcessorTypes": ["OTHER_DANGEROUS_WASTES"],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000014143",
        "companyTypes": ["WASTE_VEHICLES", "COLLECTOR"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": ["DEMOLISSEUR"],
    },
    {
        "orgId": "00000000014146",
        "companyTypes": ["PRODUCER"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000014148",
        "companyTypes": ["TRANSPORTER"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000014992",
        "companyTypes": ["WASTE_VEHICLES", "PRODUCER"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": ["BROYEUR"],
    },
    {
        "orgId": "00000000014149",
        "companyTypes": ["COLLECTOR"],
        "collectorTypes": ["DEEE_WASTES"],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000014224",
        "companyTypes": ["COLLECTOR"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000091411512",
        "companyTypes": ["WASTE_CENTER"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000094942422",
        "companyTypes": ["WASTEPROCESSOR", "COLLECTOR"],
        "collectorTypes": ["DANGEROUS_WASTES", "OTHER_NON_DANGEROUS_WASTES"],
        "wasteProcessorTypes": ["CREMATION", "DANGEROUS_WASTES_STORAGE"],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000000014455",
        "companyTypes": ["PRODUCER", "COLLECTOR"],
        "collectorTypes": ["NON_DANGEROUS_WASTES"],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
    {
        "orgId": "00000061189924",
        "companyTypes": ["DISPOSAL_FACILITY"],
        "collectorTypes": [],
        "wasteProcessorTypes": [],
        "wasteVehiclesTypes": [],
    },
]


def test_upload_update_and_convert_view_post(anon_client):
    value = signing.get_cookie_signer(salt="validator_connected").sign("connected")
    with open(MODIF_ETAB_OK, "rb") as upload:
        setattr(anon_client, "cookies", SimpleCookie({"validator_connected": value}))
        res = anon_client.post(
            reverse("validate_update_file"),
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
            follow=True,
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" not in content
    json_export = res.context["json_export"]
    json_dict = json.loads(json_export)
    assert json_dict == expected_json_dict


def test_upload_update_view_post_not_ok(anon_client):
    with open(MODIF_ETAB_NOT_OK, "rb") as upload:
        res = anon_client.post(
            reverse("validate_update_file"),
            {"file": upload, "captcha_0": 2, "captcha_1": hash_answer(2)},
            follow=True,
        )
    assert res.status_code == 200
    content = res.content.decode()

    assert "erreurs" in content
    assert "Le champ collectorTypes accepte uniquement les valeurs" in content

    errors = res.context["errors"]

    assert len(errors) == 2
    assert errors[0].row_number == 3
    assert errors[0].field_name == "wasteProcessorTypes"

    assert errors[1].row_number == 10
    assert errors[1].field_name == "collectorTypes"


def test_log_me_in(anon_client):
    url = reverse("log_me_in")

    res = anon_client.get(url)
    assert res.status_code == 200

    res = anon_client.post(url, data={"name": "joe", "password": "pass"})
    assert res.status_code == 302

    assert "validator_connected" in res.cookies.keys()
