"""Evaluation dataset and run models."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    kb_id = Column(UUID, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    questions = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="evaluation_datasets")
    runs = relationship("EvaluationRun", back_populates="dataset")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID, ForeignKey("evaluation_datasets.id"))
    name = Column(String(255))
    metrics = Column(JSON, default=dict, nullable=False)
    overall_score = Column(Float)
    status = Column(String(30), default="pending", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    dataset = relationship("EvaluationDataset", back_populates="runs")
