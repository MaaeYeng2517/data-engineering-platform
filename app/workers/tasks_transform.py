from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_transform.transform_data")
def transform_data(run_id: str):
    return {"run_id": run_id, "status": "processing"}
