"""Metadata schema model for KB field definitions and taxonomy."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class MetadataSchema(Base):
    __tablename__ = "metadata_schemas"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    kb_id = Column(UUID, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    fields = Column(JSON, default=list, nullable=False)
    taxonomy = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="metadata_schemas")
