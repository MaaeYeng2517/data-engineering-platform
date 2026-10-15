"""add website analytics tables

Revision ID: analytics_tracking_001
Revises: e853082814f9
Create Date: 2026-10-11 01:54:00.000000+00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "analytics_tracking_001"
down_revision: Union[str, None] = "e853082814f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visitors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=1000), nullable=True),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("landing_page", sa.String(length=500), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("browser", sa.String(length=100), nullable=True),
        sa.Column("os", sa.String(length=100), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False),
        sa.Column("is_authenticated", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("page_views_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visitors_first_seen", "visitors", ["first_seen_at"])
    op.create_index("ix_visitors_last_seen", "visitors", ["last_seen_at"])
    op.create_index(op.f("ix_visitors_session_id"), "visitors", ["session_id"], unique=True)
    op.create_index(op.f("ix_visitors_tenant_id"), "visitors", ["tenant_id"])
    op.create_index(op.f("ix_visitors_user_id"), "visitors", ["user_id"])
    op.create_index(op.f("ix_visitors_ip_hash"), "visitors", ["ip_hash"])

    op.create_table(
        "page_views",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visitor_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("utm_source", sa.String(length=100), nullable=True),
        sa.Column("utm_medium", sa.String(length=100), nullable=True),
        sa.Column("utm_campaign", sa.String(length=100), nullable=True),
        sa.Column("utm_term", sa.String(length=100), nullable=True),
        sa.Column("utm_content", sa.String(length=100), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["visitor_id"], ["visitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_page_views_created", "page_views", ["created_at"])
    op.create_index("ix_page_views_path_created", "page_views", ["path", "created_at"])
    op.create_index("ix_page_views_session_created", "page_views", ["session_id", "created_at"])
    op.create_index(op.f("ix_page_views_path"), "page_views", ["path"])
    op.create_index(op.f("ix_page_views_session_id"), "page_views", ["session_id"])
    op.create_index(op.f("ix_page_views_tenant_id"), "page_views", ["tenant_id"])
    op.create_index(op.f("ix_page_views_user_id"), "page_views", ["user_id"])
    op.create_index(op.f("ix_page_views_visitor_id"), "page_views", ["visitor_id"])

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visitor_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("section", sa.String(length=100), nullable=True),
        sa.Column("feature", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=True),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=1000), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["visitor_id"], ["visitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_events_created", "analytics_events", ["created_at"])
    op.create_index("ix_analytics_events_type_created", "analytics_events", ["event_type", "created_at"])
    op.create_index("ix_analytics_events_section_created", "analytics_events", ["section", "created_at"])
    op.create_index(op.f("ix_analytics_events_event_type"), "analytics_events", ["event_type"])
    op.create_index(op.f("ix_analytics_events_section"), "analytics_events", ["section"])
    op.create_index(op.f("ix_analytics_events_path"), "analytics_events", ["path"])
    op.create_index(op.f("ix_analytics_events_session_id"), "analytics_events", ["session_id"])
    op.create_index(op.f("ix_analytics_events_tenant_id"), "analytics_events", ["tenant_id"])
    op.create_index(op.f("ix_analytics_events_user_id"), "analytics_events", ["user_id"])
    op.create_index(op.f("ix_analytics_events_visitor_id"), "analytics_events", ["visitor_id"])

    op.create_table(
        "subscribers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False),
        sa.Column("consent_at", sa.DateTime(), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(), nullable=True),
        sa.Column("double_opt_in", sa.Boolean(), nullable=False),
        sa.Column("double_opt_in_at", sa.DateTime(), nullable=True),
        sa.Column("confirmation_token", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=1000), nullable=True),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("landing_page", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscribers_created", "subscribers", ["created_at"])
    op.create_index(op.f("ix_subscribers_email"), "subscribers", ["email"], unique=True)
    op.create_index(op.f("ix_subscribers_status"), "subscribers", ["status"])
    op.create_index(op.f("ix_subscribers_source"), "subscribers", ["source"])
    op.create_index(op.f("ix_subscribers_tenant_id"), "subscribers", ["tenant_id"])

    op.create_table(
        "usage_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("visitor_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("section", sa.String(length=100), nullable=False),
        sa.Column("feature", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["visitor_id"], ["visitors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_created", "usage_events", ["created_at"])
    op.create_index("ix_usage_events_section_created", "usage_events", ["section", "created_at"])
    op.create_index("ix_usage_events_feature_created", "usage_events", ["feature", "created_at"])
    op.create_index(op.f("ix_usage_events_section"), "usage_events", ["section"])
    op.create_index(op.f("ix_usage_events_feature"), "usage_events", ["feature"])
    op.create_index(op.f("ix_usage_events_action"), "usage_events", ["action"])
    op.create_index(op.f("ix_usage_events_path"), "usage_events", ["path"])
    op.create_index(op.f("ix_usage_events_session_id"), "usage_events", ["session_id"])
    op.create_index(op.f("ix_usage_events_tenant_id"), "usage_events", ["tenant_id"])
    op.create_index(op.f("ix_usage_events_user_id"), "usage_events", ["user_id"])
    op.create_index(op.f("ix_usage_events_visitor_id"), "usage_events", ["visitor_id"])


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("subscribers")
    op.drop_table("analytics_events")
    op.drop_table("page_views")
    op.drop_table("visitors")
