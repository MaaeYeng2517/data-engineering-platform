"""External API integration model for managing outbound API connections."""
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class ExternalAPI(Base):
    __tablename__ = "external_apis"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), nullable=False)
    description = Column(Text)
    base_url = Column(String(500), nullable=False)
    auth_type = Column(String(20), default="none")  # none, api_key, bearer, basic, oauth2
    auth_config = Column(JSON, default=dict)
    headers = Column(JSON, default=dict)
    rate_limit = Column(Integer, default=60)  # requests per minute
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime)
    last_test_status = Column(String(20))  # ok, failed
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="external_apis")

    def __repr__(self):
        return f"<ExternalAPI {self.name}>"