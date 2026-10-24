from fastapi import APIRouter

router = APIRouter()


@router.post("/checks")
async def run_quality_check():
    return {"message": "quality check queued"}


@router.get("/{dataset_id}")
async def get_lineage(dataset_id: str):
    return {"nodes": [], "edges": []}
