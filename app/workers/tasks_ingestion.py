from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_ingestion.ingest_file")
def ingest_file(job_id: str, dataset_id: str):
    return {"job_id": job_id, "status": "processing"}
