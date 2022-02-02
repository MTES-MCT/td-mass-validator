import httpx

SOCIAL_GOUV_API_BASE_URL = (
    "https://search-recherche-entreprises.fabrique.social.gouv.fr"
)


def check_siret(siret):
    r = httpx.get(f"{SOCIAL_GOUV_API_BASE_URL}/api/v1/etablissement/{siret}")

    if r.status_code == 200:
        return True
    return False
