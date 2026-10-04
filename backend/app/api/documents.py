"""Documents API endpoints"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas import DocumentCreate, DocumentResponse

router = APIRouter()

# In-memory storage
_documents = {}


def _get_scoped(doc_id: str, user: User) -> dict:
    """Return the document only if it belongs to the caller's workspace."""
    record = _documents.get(doc_id)
    if record is None or record["tenant_id"] != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return record


@router.post("/", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    user: User = Depends(get_current_user),
):
    """Create a new document"""
    doc_id = str(uuid.uuid4())

    new_doc = {
        "id": doc_id,
        "kb_id": str(doc.kb_id),
        "tenant_id": str(user.tenant_id),
        "created_by": str(user.id),
        "title": doc.title,
        "source_type": doc.source_type,
        "source_url": doc.source_url,
        "status": "pending",
        "version": "1.0",
        "is_published": False,
        "created_at": utcnow()
    }

    _documents[doc_id] = new_doc
    return new_doc


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    kb_id: str = Form(...),
    title: str = Form(None),
    user: User = Depends(get_current_user),
):
    """Upload a document file into a knowledge base.

    ``kb_id`` and ``title`` are read as form fields because multipart uploads
    cannot carry a JSON body; a query parameter would be silently ignored.
    """
    doc_id = str(uuid.uuid4())

    # Read file content
    content = await file.read()

    new_doc = {
        "id": doc_id,
        "kb_id": kb_id,
        "tenant_id": str(user.tenant_id),
        "created_by": str(user.id),
        "title": title or file.filename,
        "source_type": "file",
        "source_url": None,
        "status": "processing",
        "version": "1.0",
        "is_published": False,
        "created_at": utcnow(),
        "file_size": len(content),
        "mime_type": file.content_type
    }

    _documents[doc_id] = new_doc

    from backend.app.services.processing import processing_engine

    # Extract text, chunk and derive entities so the record is immediately searchable.
    content_str = content.decode('utf-8', errors='ignore')
    result = await processing_engine.process(content_str, "file")

    _documents[doc_id]["status"] = "processed"
    _documents[doc_id]["content"] = result["extracted"]
    _documents[doc_id]["chunks"] = result["chunks"]
    _documents[doc_id]["entities"] = result["entities"]

    return new_doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(kb_id: str = None, user: User = Depends(get_current_user)):
    """List documents in the caller's workspace, optionally filtered by knowledge base"""
    docs = [
        record for record in _documents.values()
        if record["tenant_id"] == str(user.tenant_id)
    ]
    if kb_id:
        docs = [record for record in docs if record["kb_id"] == kb_id]
    return docs


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, user: User = Depends(get_current_user)):
    """Get document by ID"""
    return _get_scoped(doc_id, user)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user: User = Depends(get_current_user)):
    """Delete document"""
    _get_scoped(doc_id, user)

    del _documents[doc_id]
    return {"message": "Document deleted"}