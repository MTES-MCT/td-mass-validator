import time

import httpx

SOCIAL_GOUV_API_BASE_URL = (
    "https://search-recherche-entreprises.fabrique.social.gouv.fr"
)

ACTIVE = "A"


def check_siret(siret):
    """Check siret exists and is not closed"""
    try:
        # default 5s timeout
        r = httpx.get(f"{SOCIAL_GOUV_API_BASE_URL}/api/v1/etablissement/{siret}")
    except httpx.RequestError:
        return False
    time.sleep(0.05)  # let api rest a little
    if (
        r.status_code == 200
        and r.json().get("etatAdministratifEtablissement") == ACTIVE
    ):
        return True
    return False
