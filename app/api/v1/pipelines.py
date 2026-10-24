from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_pipeline():
    return {"message": "pipeline created"}


@router.post("/{pipeline_id}/runs")
async def run_pipeline(pipeline_id: str):
    return {"run_id": "run_123", "status": "queued"}
