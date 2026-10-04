"""Metadata API endpoints"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas import MetadataSchemaCreate, MetadataSchemaResponse

router = APIRouter()

# In-memory storage
_schemas = {}


@router.post("/", response_model=MetadataSchemaResponse)
async def create_schema(
    schema: MetadataSchemaCreate,
    user: User = Depends(get_current_user),
):
    """Create a metadata schema"""
    schema_id = str(uuid.uuid4())

    new_schema = {
        "id": schema_id,
        "kb_id": str(schema.kb_id),
        "tenant_id": str(user.tenant_id),
        "created_by": str(user.id),
        "name": schema.name,
        "description": schema.description,
        "fields": schema.fields,
        "taxonomy": schema.taxonomy,
        "is_active": True,
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

    _schemas[schema_id] = new_schema
    return new_schema


@router.get("/", response_model=List[MetadataSchemaResponse])
async def list_schemas(kb_id: str = None, user: User = Depends(get_current_user)):
    """List metadata schemas in the caller's workspace"""
    schemas = [
        record for record in _schemas.values()
        if record["tenant_id"] == str(user.tenant_id)
    ]
    if kb_id:
        schemas = [record for record in schemas if record["kb_id"] == kb_id]
    return schemas


@router.get("/{schema_id}", response_model=MetadataSchemaResponse)
async def get_schema(schema_id: str, user: User = Depends(get_current_user)):
    """Get schema by ID"""
    return _get_scoped(schema_id, user)


@router.put("/{schema_id}", response_model=MetadataSchemaResponse)
async def update_schema(
    schema_id: str,
    schema: MetadataSchemaCreate,
    user: User = Depends(get_current_user),
):
    """Update schema"""
    record = _get_scoped(schema_id, user)

    record.update({
        "name": schema.name,
        "description": schema.description,
        "fields": schema.fields,
        "taxonomy": schema.taxonomy,
        "updated_at": utcnow()
    })

    return record


@router.delete("/{schema_id}")
async def delete_schema(schema_id: str, user: User = Depends(get_current_user)):
    """Delete schema"""
    _get_scoped(schema_id, user)

    del _schemas[schema_id]
    return {"message": "Schema deleted"}


@router.post("/{schema_id}/validate")
async def validate_data(schema_id: str, data: dict, user: User = Depends(get_current_user)):
    """Validate data against schema"""
    _get_scoped(schema_id, user)

    from backend.app.services.metadata import metadata_engine

    result = metadata_engine.validate(schema_id, data)
    return result


def _get_scoped(schema_id: str, user: User) -> dict:
    """Return the schema only if it belongs to the caller's workspace."""
    record = _schemas.get(schema_id)
    if record is None or record["tenant_id"] != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Schema not found")
    return record