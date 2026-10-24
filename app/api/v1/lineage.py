from fastapi import APIRouter

router = APIRouter()


@router.get("/{dataset_id}")
async def get_lineage(dataset_id: str):
    return {"nodes": [], "edges": []}
