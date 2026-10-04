"""Contact message model for the public contact form."""
import enum
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class ContactStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    SPAM = "spam"


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    name = Column(String(100), nullable=False)
    email = Column(String(320), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(30), default=ContactStatus.NEW.value, nullable=False, index=True)
    admin_notes = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(1000))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="contact_messages", foreign_keys=[user_id])
    tenant = relationship("Tenant", back_populates="contact_messages")
    resolver = relationship("User", foreign_keys=[resolved_by])
