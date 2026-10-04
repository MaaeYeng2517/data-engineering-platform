"""Work group models: teams of users organised within a tenant."""
import enum
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class WorkGroupRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class WorkGroup(Base):
    """A team of users inside a tenant, used to scope collaboration."""

    __tablename__ = "work_groups"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(String(1000))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    tenant = relationship("Tenant", back_populates="work_groups")
    members = relationship(
        "WorkGroupMember",
        back_populates="work_group",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_work_groups_tenant_slug"),
    )


class WorkGroupMember(Base):
    """Join record linking a user to a work group."""

    __tablename__ = "work_group_members"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    work_group_id = Column(
        UUID, ForeignKey("work_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(30), default=WorkGroupRole.MEMBER.value, nullable=False)
    joined_at = Column(DateTime, default=utcnow, nullable=False)

    work_group = relationship("WorkGroup", back_populates="members")
    user = relationship("User", back_populates="work_group_memberships")

    __table_args__ = (
        UniqueConstraint("work_group_id", "user_id", name="uq_work_group_members"),
    )