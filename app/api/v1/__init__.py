from fastapi import APIRouter

from app.api.v1 import health, datasets, jobs, pipelines, quality, lineage, audit, events, visualization

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
api_router.include_router(quality.router, prefix="/quality", tags=["Quality"])
api_router.include_router(lineage.router, prefix="/lineage", tags=["Lineage"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["Visualization"])
