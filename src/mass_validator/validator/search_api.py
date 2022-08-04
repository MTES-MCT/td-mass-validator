from django.conf import settings
from elasticsearch7 import Elasticsearch

ACTIVE = "A"

CERT_PATH = "certs.pem"
es = Elasticsearch(settings.TD_COMPANY_ELASTICSEARCH_URL, ca_certs=CERT_PATH)


def check_siret(siret):
    body = {"query": {"bool": {"must": [{"match": {"siret": siret}}]}}}
    resp = es.search(index=settings.TD_COMPANY_ELASTICSEARCH_INDEX, body=body)
    try:
        hits = resp["hits"]["hits"]
    except IndexError:
        return False
    for hit in hits:
        if hit.get("_source", {}).get("etatAdministratifEtablissement", None) == ACTIVE:
            return True
    return False
