"""Alembic environment, wired for the project's async SQLAlchemy stack.

The application talks to Postgres through ``postgresql+asyncpg://`` and declares
its models on the ``declarative_base()`` in ``backend/database.py``, so this
environment overrides ``sqlalchemy.url`` with the same ``DATABASE_URL`` the app
uses and drives migrations with ``async_engine_from_config``. Both offline
(``--sql``) and online modes are supported.
"""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic is invoked from the repo root (`alembic` is not installed as a package),
# so make sure the `backend` package is importable no matter the working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# These imports are deliberately below the sys.path fixup above, hence noqa: E402.
# Importing ``backend.app.models`` is what registers every table on
# ``Base.metadata``; autogenerate diffs against it below.
from backend.app import models as _models  # noqa: E402,F401
from backend.config import DATABASE_URL  # noqa: E402
from backend.database import Base  # noqa: E402

target_metadata = Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The placeholder in alembic.ini is replaced here so the connection always
# follows the application's own environment variable.
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def _common_options() -> dict:
    """Settings shared by the offline and online migration contexts."""
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
    }


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a DBAPI connection (``alembic upgrade --sql``)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_common_options(),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run the migrations on an already-established synchronous connection."""
    context.configure(connection=connection, **_common_options())

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and hand a sync connection to the runner."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Drive ``run_async_migrations`` from a synchronous entry point."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
