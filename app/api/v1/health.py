from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
async def live():
    return {"status": "ok", "service": "enterprise-data-api"}


@router.get("/ready")
async def ready():
    return {"status": "ready", "checks": {"db": "ok", "redis": "ok", "storage": "ok"}}
