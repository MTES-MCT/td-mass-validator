from unittest.mock import patch

import pytest

from ..tasks import check_sirets

pytestmark = pytest.mark.django_db


@patch("mass_validator.tasks.check_siret")
def test_check_sirets_fails(mock_get):
    mock_get.return_value = False

    res = check_sirets([{"siret": "1234"}])

    assert res == [{"siret": "1234"}]


@patch("mass_validator.tasks.check_siret")
def test_check_sirets_succeeds(mock_get):
    mock_get.return_value = True

    res = check_sirets([{"siret": "1234"}])

    assert res == []
