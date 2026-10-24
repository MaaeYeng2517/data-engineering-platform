from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def ingest_event():
    return {"status": "accepted"}
