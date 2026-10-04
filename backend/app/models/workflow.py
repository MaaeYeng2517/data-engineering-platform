"""Workflow model for KB processing graphs."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    kb_id = Column(UUID, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    nodes = Column(JSON, default=list, nullable=False)
    edges = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="workflows")
