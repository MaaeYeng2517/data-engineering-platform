from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_quality.run_checks")
def run_checks(dataset_id: str):
    return {"dataset_id": dataset_id, "status": "processing"}
