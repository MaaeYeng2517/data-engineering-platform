"""Service profile models.

A profile is one environment (development, staging, production, …) on one cloud
or hosting target. It carries the arbitrary configuration for that environment
plus the services reachable from it, each with its own endpoint, auth style and
encrypted token.
"""
import enum
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class ProfileEnvironment(str, enum.Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class CloudProvider(str, enum.Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"
    OTHER = "other"


class ServiceType(str, enum.Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    VECTOR_DB = "vector_db"
    SEARCH = "search"
    OBJECT_STORAGE = "object_storage"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    MONITORING = "monitoring"
    CDN = "cdn"
    OTHER = "other"


class AuthType(str, enum.Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    MTLS = "mtls"
    CUSTOM = "custom"


class ServiceHealth(str, enum.Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=False)
    description = Column(Text)
    environment = Column(
        String(30),
        default=ProfileEnvironment.DEVELOPMENT.value,
        nullable=False,
    )
    cloud_provider = Column(
        String(30),
        default=CloudProvider.OTHER.value,
        nullable=False,
    )
    region = Column(String(60))
    zone = Column(String(60))
    # Non-secret environment variables for the whole profile.
    variables = Column(JSON, default=dict, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    services = relationship(
        "ProfileService",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProfileService.name",
    )
    config_items = relationship(
        "ProfileConfigItem",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProfileConfigItem.key",
    )


class ProfileService(Base):
    """One reachable service inside a profile, with its endpoint and token."""

    __tablename__ = "profile_services"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    service_type = Column(String(40), default=ServiceType.OTHER.value, nullable=False)
    provider = Column(String(80))
    description = Column(Text)
    # Where the service lives: API base URL, or host/port for a self-hosted one.
    api_base_url = Column(String(500))
    host = Column(String(255))
    port = Column(Integer)
    region = Column(String(60))
    zone = Column(String(60))
    auth_type = Column(String(30), default=AuthType.API_KEY.value, nullable=False)
    # Fernet ciphertext. Never serialised to a client.
    token_encrypted = Column(Text)
    username = Column(String(255))
    # Fernet ciphertext of a JSON object for any extra provider credentials.
    credentials_encrypted = Column(Text)
    env_vars = Column(JSON, default=dict, nullable=False)
    headers = Column(JSON, default=dict, nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    health_check_url = Column(String(500))
    health_check_enabled = Column(Boolean, default=False, nullable=False)
    health_status = Column(String(20), default=ServiceHealth.UNKNOWN.value, nullable=False)
    last_checked_at = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    profile = relationship("Profile", back_populates="services")


class ProfileConfigItem(Base):
    """A single configuration key inside a profile."""

    __tablename__ = "profile_config_items"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False, index=True)
    key = Column(String(120), nullable=False)
    value = Column(Text)
    description = Column(Text)
    value_type = Column(String(20), default="string", nullable=False)
    # Secret values are Fernet ciphertext in `value`; the plaintext is never
    # returned by list or detail responses.
    is_secret = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    profile = relationship("Profile", back_populates="config_items")
