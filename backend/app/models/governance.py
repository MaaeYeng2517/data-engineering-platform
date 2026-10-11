"""Governance policy and approval models."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class GovernancePolicy(Base):
    """A governance policy with rules that can be evaluated against data."""

    __tablename__ = "governance_policies"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rules = Column(JSON, default=dict, nullable=False)
    version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="governance_policies")
    creator = relationship("User", back_populates="governance_policies")


class ApprovalWorkflow(Base):
    """An approval workflow for documents or changes."""

    __tablename__ = "approval_workflows"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    kb_id = Column(UUID, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    document_id = Column(UUID, ForeignKey("documents.id"), nullable=False, index=True)
    creator_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    reviewers = Column(ARRAY(UUID), default=list, nullable=False)
    status = Column(String(30), default="pending", nullable=False)  # pending, approved, rejected
    decision = Column(String(30))  # approved, rejected
    comments = Column(Text)
    decided_by = Column(UUID, ForeignKey("users.id"))
    decided_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="approval_workflows")
    knowledge_base = relationship("KnowledgeBase", back_populates="approval_workflows")
    document = relationship("Document", back_populates="approval_workflows")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_approvals")
    decider = relationship("User", foreign_keys=[decided_by], back_populates="decided_approvals")