"""Website analytics and statistics models."""
import enum
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.utils.time import utcnow
from backend.database import Base


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    ip_hash = Column(String(64), nullable=True, index=True)
    user_agent = Column(String(1000), nullable=True)
    referrer = Column(String(500), nullable=True)
    landing_page = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    is_bot = Column(Boolean, default=False, nullable=False)
    is_authenticated = Column(Boolean, default=False, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    first_seen_at = Column(DateTime, default=utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    page_views_count = Column(Integer, default=0, nullable=False)

    tenant = relationship("Tenant", back_populates="visitors")
    user = relationship("User", back_populates="visitors")
    page_views = relationship("PageView", back_populates="visitor", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="visitor", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="visitor")

    __table_args__ = (
        Index("ix_visitors_first_seen", "first_seen_at"),
        Index("ix_visitors_last_seen", "last_seen_at"),
    )


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    visitor_id = Column(UUID, ForeignKey("visitors.id"), nullable=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    path = Column(String(500), nullable=False, index=True)
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    visitor = relationship("Visitor", back_populates="page_views")
    user = relationship("User", back_populates="page_views")
    tenant = relationship("Tenant", back_populates="page_views")

    __table_args__ = (
        Index("ix_page_views_path_created", "path", "created_at"),
        Index("ix_page_views_created", "created_at"),
        Index("ix_page_views_session_created", "session_id", "created_at"),
    )


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    visitor_id = Column(UUID, ForeignKey("visitors.id"), nullable=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True, index=True)
    session_id = Column(String(255), index=True, nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    section = Column(String(100), nullable=True, index=True)
    feature = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=True, index=True)
    path = Column(String(500), nullable=True, index=True)
    label = Column(String(255), nullable=True)
    value = Column(Integer, nullable=True)
    properties = Column(JSON, default=dict, nullable=False)
    referrer = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(1000), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    visitor = relationship("Visitor", back_populates="analytics_events")
    user = relationship("User", back_populates="analytics_events")
    tenant = relationship("Tenant", back_populates="analytics_events")

    __table_args__ = (
        Index("ix_analytics_events_type_created", "event_type", "created_at"),
        Index("ix_analytics_events_section_created", "section", "created_at"),
        Index("ix_analytics_events_created", "created_at"),
    )


class SubscriberStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    SPAM = "spam"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(320), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True, index=True)
    status = Column(String(30), default=SubscriberStatus.ACTIVE.value, nullable=False, index=True)
    source = Column(String(100), nullable=True, index=True)
    consent_given = Column(Boolean, default=True, nullable=False)
    consent_at = Column(DateTime, default=utcnow, nullable=False)
    unsubscribed_at = Column(DateTime, nullable=True)
    double_opt_in = Column(Boolean, default=False, nullable=False)
    double_opt_in_at = Column(DateTime, nullable=True)
    confirmation_token = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(1000), nullable=True)
    referrer = Column(String(500), nullable=True)
    landing_page = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="subscribers")

    __table_args__ = (Index("ix_subscribers_created", "created_at"),)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True, index=True)
    visitor_id = Column(UUID, ForeignKey("visitors.id"), nullable=True, index=True)
    session_id = Column(String(255), index=True, nullable=True)
    section = Column(String(100), nullable=False, index=True)
    feature = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    path = Column(String(500), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)
    meta = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="usage_events")
    tenant = relationship("Tenant", back_populates="usage_events")
    visitor = relationship("Visitor", back_populates="usage_events")

    __table_args__ = (
        Index("ix_usage_events_section_created", "section", "created_at"),
        Index("ix_usage_events_feature_created", "feature", "created_at"),
        Index("ix_usage_events_created", "created_at"),
    )
