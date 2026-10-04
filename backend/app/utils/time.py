"""UTC timestamps.

Every timestamp column in this schema is a plain ``TIMESTAMP WITHOUT TIME ZONE``
and asyncpg refuses to store an offset-aware datetime into one, so application
code stores naive UTC. Keeping that decision in one helper means the eventual
migration to ``timestamptz`` is a single change here rather than 100 call sites.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching the database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
