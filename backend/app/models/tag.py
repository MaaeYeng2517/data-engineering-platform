"""Tag model for categorizing knowledge bases, documents, and data sources."""
import uuid
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(60), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    kbs = relationship("KnowledgeBase", secondary="tag_kb_association", back_populates="tags")
    documents = relationship("Document", secondary="tag_document_association", back_populates="tags")
    sources = relationship("Source", secondary="tag_source_association", back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


# Association tables for many-to-many relationships
from sqlalchemy import Table, ForeignKey

tag_kb_association = Table(
    "tag_kb_association",
    Base.metadata,
    Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
    Column("kb_id", UUID, ForeignKey("knowledge_bases.id"), primary_key=True),
)

tag_document_association = Table(
    "tag_document_association",
    Base.metadata,
    Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
    Column("document_id", UUID, ForeignKey("documents.id"), primary_key=True),
)

tag_source_association = Table(
    "tag_source_association",
    Base.metadata,
    Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
    Column("source_id", UUID, ForeignKey("sources.id"), primary_key=True),
)