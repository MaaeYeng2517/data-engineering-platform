"""MinIO object storage client."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)

logger = logging.getLogger(__name__)


def _client():
    import boto3
    from botocore.config import Config

    endpoint = f"{'https' if MINIO_SECURE else 'http'}://{MINIO_ENDPOINT}"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(s3={"addressing_style": "path"}),
    )


async def get_health() -> Dict[str, Any]:
    try:
        client = _client()
        client.list_buckets()
        return {"status": "healthy", "endpoint": MINIO_ENDPOINT}
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc)}


async def list_buckets() -> List[Dict[str, Any]]:
    try:
        client = _client()
        return [
            {
                "name": bucket.get("Name"),
                "created_at": bucket.get("CreationDate").isoformat()
                if isinstance(bucket.get("CreationDate"), datetime)
                else str(bucket.get("CreationDate")),
            }
            for bucket in client.list_buckets().get("Buckets", [])
        ]
    except Exception as exc:
        logger.warning("MinIO list_buckets failed: %s", exc)
        return []


async def list_objects(bucket: Optional[str] = None, prefix: str = "", limit: int = 100) -> Dict[str, Any]:
    target = bucket or MINIO_BUCKET
    try:
        client = _client()
        paginator = client.get_paginator("list_objects_v2")
        objects: List[Dict[str, Any]] = []
        for page in paginator.paginate(Bucket=target, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects.append(
                    {
                        "key": obj.get("Key"),
                        "size": obj.get("Size"),
                        "last_modified": obj.get("LastModified").isoformat()
                        if isinstance(obj.get("LastModified"), datetime)
                        else str(obj.get("LastModified")),
                        "etag": obj.get("ETag"),
                        "storage_class": obj.get("StorageClass"),
                        "url": f"/api/v1/storage/objects/{target}/{obj.get('Key')}",
                    }
                )
                if len(objects) >= limit:
                    break
            if len(objects) >= limit:
                break
        return {"bucket": target, "count": len(objects), "objects": objects}
    except Exception as exc:
        logger.warning("MinIO list_objects failed: %s", exc)
        return {"bucket": target, "count": 0, "objects": [], "error": str(exc)}


async def get_bucket_stats() -> List[Dict[str, Any]]:
    stats = []
    for bucket in await list_buckets():
        result = await list_objects(bucket=bucket["name"], limit=1000)
        total_size = sum(obj.get("size") or 0 for obj in result.get("objects", []))
        stats.append(
            {
                "name": bucket["name"],
                "object_count": result.get("count", 0),
                "total_size": total_size,
            }
        )
    return stats
