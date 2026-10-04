"""Public contact form endpoint and the caller's own message history."""
import logging
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_optional_user, require_platform_user
from backend.app.models.contact import ContactMessage, ContactStatus
from backend.app.models.user import User
from backend.app.schemas import ContactMessageCreate, ContactMessageResponse
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/contact", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_message(
    payload: ContactMessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Accept a contact message from anonymous or authenticated visitors."""
    message = ContactMessage(
        user_id=user.id if user else None,
        tenant_id=user.tenant_id if user else None,
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        status=ContactStatus.NEW.value,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    logger.info("Stored contact message %s", message.id)
    return message


@router.get("/contact/mine", response_model=List[ContactMessageResponse])
async def list_my_contact_messages(
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the contact messages the signed-in user submitted, newest first."""
    result = await db.execute(
        select(ContactMessage)
        .where(ContactMessage.user_id == user.id)
        .order_by(ContactMessage.created_at.desc())
    )
    return list(result.scalars().all())