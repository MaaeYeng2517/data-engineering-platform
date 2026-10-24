from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_dataset():
    return {"message": "create dataset endpoint"}


@router.get("/")
async def list_datasets():
    return {"items": [], "total": 0, "page": 1, "limit": 20}


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    return {"id": dataset_id}


@router.post("/{dataset_id}/upload-sessions")
async def create_upload_session(dataset_id: str):
    return {"upload_url": "https://storage.example.com/upload", "expires_in": 3600}


@router.post("/{dataset_id}/versions")
async def register_version(dataset_id: str):
    return {"message": "version registered"}
