from celery import current_task

from core.celery_app import app
from mass_validator.validator.search_api import check_siret


@app.task
def check_sirets(data):
    """
    Pollable task to check siret existence and validity on api.

    :param data: {"siret": row.siret, "row_number": row.index}
    """
    errors = []
    count = len(data)
    for idx, el in enumerate(data):
        siret_exists = check_siret(el["siret"])

        current_task.update_state(
            state="PROGRESS", meta={"progress": round(100 * ((idx + 1) / count))}
        )

        if not siret_exists:
            errors.append(el)
    current_task.update_state(state="DONE", meta={"progress": 100})

    return errors
