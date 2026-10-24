from fastapi import APIRouter, status

router = APIRouter()


@router.post("/ingestion", status_code=status.HTTP_202_ACCEPTED)
async def create_ingestion_job():
    return {"job_id": "job_01JXYZ789", "status": "queued", "status_url": "/api/v1/jobs/job_01JXYZ789"}


@router.get("/{job_id}")
async def get_job(job_id: str):
    return {"job_id": job_id, "status": "queued", "attempt_count": 0}
