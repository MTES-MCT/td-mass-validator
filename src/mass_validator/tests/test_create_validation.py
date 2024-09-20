from ..validator.row_models import EtabCreateRow


def test_etab():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": None,
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert etab_row.is_valid


def test_etab_wp_1():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": None,
        "wasteProcessorTypes": ["PLOP"],
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_wp_2():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": None,
        "wasteProcessorTypes": ["OTHER_DANGEROUS_WASTES"],
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_wp_3():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER", "WASTEPROCESSOR"],
        "collectorTypes": None,
        "wasteProcessorTypes": ["OTHER_DANGEROUS_WASTES"],
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert etab_row.is_valid


def test_etab_coll_1():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": ["PLOP"],
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_coll_2():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": [
            "DEEE_WASTES",
        ],
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_coll_3():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": [
            "PRODUCER",
            "COLLECTOR",
        ],
        "collectorTypes": [
            "DEEE_WASTES",
        ],
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": None,
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert etab_row.is_valid


def test_etab_vhl_1():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": None,
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": ["PLOP"],
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_vhl_2():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": ["PRODUCER"],
        "collectorTypes": None,
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": ["BROYEUR"],
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert not etab_row.is_valid


def test_etab_vhl_3():
    row = {
        "siret": "1OO00000000048",
        "gerepId": None,
        "companyTypes": [
            "PRODUCER",
            "WASTE_VEHICLES",
        ],
        "collectorTypes": None,
        "wasteProcessorTypes": None,
        "wasteVehiclesTypes": ["BROYEUR"],
        "givenName": "Name",
    }
    etab_row = EtabCreateRow.from_dict(1, row)
    etab_row.validate()
    assert etab_row.is_valid
