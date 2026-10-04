"""Application configuration."""
import json
import logging
import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent

_TRUTHY = {"1", "true", "yes", "on"}


def _env_flag(name: str, default: bool) -> bool:
    """Read a boolean environment variable, falling back when it is unset."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in _TRUTHY


def _env_text(name: str, default: str) -> str:
    """Read a text variable, treating a blank value as unset."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw


APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV in {"production", "prod"}
DEBUG = os.getenv("DEBUG", "false" if IS_PRODUCTION else "true").lower() == "true"
APP_NAME = os.getenv("APP_NAME", "Knowledge Engineering Platform")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ke_user:ke_password@localhost:5432/knowledge_platform",
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "dataair")

# --- Platform integrations -------------------------------------------------
AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://localhost:8080").rstrip("/")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
AIRFLOW_PUBLIC_URL = os.getenv("AIRFLOW_PUBLIC_URL", AIRFLOW_URL).rstrip("/")
OPENMETADATA_URL = os.getenv("OPENMETADATA_URL", "http://localhost:8585").rstrip("/")
OPENMETADATA_USERNAME = os.getenv("OPENMETADATA_USERNAME", "admin@dataair.local")
OPENMETADATA_PASSWORD = os.getenv("OPENMETADATA_PASSWORD", "admin")
OPENMETADATA_PUBLIC_URL = os.getenv("OPENMETADATA_PUBLIC_URL", OPENMETADATA_URL).rstrip("/")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
PROMETHEUS_PUBLIC_URL = os.getenv("PROMETHEUS_PUBLIC_URL", PROMETHEUS_URL).rstrip("/")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3001").rstrip("/")
GRAFANA_PUBLIC_URL = os.getenv("GRAFANA_PUBLIC_URL", GRAFANA_URL).rstrip("/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_EMBEDDING_MODEL = os.getenv("LLM_EMBEDDING_MODEL", "text-embedding-3-small")

# --- LLM providers ---------------------------------------------------------
# Every provider is optional. The gateway picks the first configured one and
# falls back to a deterministic offline responder so development, CI and the
# marketing site keep working without any credential.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_OFFLINE_FALLBACK = _env_flag("LLM_OFFLINE_FALLBACK", True)
LLM_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "60"))
LLM_MODEL_CACHE_TTL = int(os.getenv("LLM_MODEL_CACHE_TTL", "300"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", LLM_MODEL)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
GOOGLE_API_BASE = os.getenv(
    "GOOGLE_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
).rstrip("/")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# --- Chat ------------------------------------------------------------------
CHAT_SYSTEM_PROMPT = _env_text(
    "CHAT_SYSTEM_PROMPT",
    "You are DataAir's assistant for an enterprise data operating platform. "
    "Answer concisely and concretely. DataAir covers the full data lifecycle: "
    "ingestion, knowledge bases, hybrid search, retrieval augmented generation, "
    "workflow orchestration, data lineage, governance and evaluation. "
    "When a question depends on the user's own data and no grounding context is "
    "provided, say what they should connect or ask instead of inventing results.",
)
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.4"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1024"))
CHAT_MAX_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "20"))
CHAT_MAX_MESSAGE_CHARS = int(os.getenv("CHAT_MAX_MESSAGE_CHARS", "4000"))
CHAT_MAX_CONTEXT_CHARS = int(os.getenv("CHAT_MAX_CONTEXT_CHARS", "6000"))
CHAT_RATE_LIMIT_REQUESTS = int(os.getenv("CHAT_RATE_LIMIT_REQUESTS", "20"))
CHAT_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("CHAT_RATE_LIMIT_WINDOW_SECONDS", "60"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-me-1234567890abcdef")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", FRONTEND_URL).rstrip("/")
ALLOWED_ORIGINS_VALUE = os.getenv("ALLOWED_ORIGINS", FRONTEND_URL)
ALLOWED_ORIGINS = list(
    dict.fromkeys(
        origin.strip()
        for origin in ALLOWED_ORIGINS_VALUE.split(",")
        if origin.strip()
    )
)
if FRONTEND_URL not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.insert(0, FRONTEND_URL)


def _localhost_variants(origin: str) -> list[str]:
    """Return the loopback spelling variants of a localhost origin.

    Browsers treat ``localhost`` and ``127.0.0.1`` as distinct origins, so a
    frontend opened on one is rejected by CORS when only the other is listed.
    The two are interchangeable for local development, so allow both.
    """
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(origin)
    if parts.hostname != "localhost":
        return []

    variants = []
    for host in ("127.0.0.1", "[::1]"):
        netloc = f"{host}:{parts.port}" if parts.port else host
        variants.append(urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)))
    return variants


for _origin in list(ALLOWED_ORIGINS):
    for _variant in _localhost_variants(_origin):
        if _variant not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(_variant)

ADMIN_EMAILS = [
    email.strip().lower()
    for email in os.getenv("ADMIN_EMAILS", "").split(",")
    if email.strip()
]
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if IS_PRODUCTION else "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("COOKIE_SAMESITE must be lax, strict, or none")
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", "development-only-change-me-1234567890abcdef")
API_KEY_HMAC_SECRET = os.getenv("API_KEY_HMAC_SECRET", "development-only-change-me-1234567890abcdef")

# Service profiles store provider tokens and credentials encrypted at rest. This
# key derives the Fernet key, so rotating it makes every stored secret unreadable.
PROFILE_SECRET_KEY = _env_text(
    "PROFILE_SECRET_KEY",
    "development-only-change-me-1234567890abcdef",
)
# Secrets are write-only through the API; revealing one is a deliberate,
# admin-only act.
PROFILE_SECRET_REVEAL_ENABLED = _env_flag("PROFILE_SECRET_REVEAL_ENABLED", True)
PROFILE_HEALTH_CHECK_TIMEOUT_SECONDS = float(
    os.getenv("PROFILE_HEALTH_CHECK_TIMEOUT_SECONDS", "5")
)
PROFILE_HEALTH_CHECK_MAX_TIMEOUT_SECONDS = float(
    os.getenv("PROFILE_HEALTH_CHECK_MAX_TIMEOUT_SECONDS", "15")
)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL",
    f"{FRONTEND_URL}/billing?checkout=success",
)
STRIPE_CANCEL_URL = os.getenv(
    "STRIPE_CANCEL_URL",
    f"{FRONTEND_URL}/billing?checkout=cancelled",
)
STRIPE_FREE_PRICE_ID = os.getenv("STRIPE_FREE_PRICE_ID", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_ENTERPRISE_PRICE_ID = os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "")


def _configured_plans() -> list[dict[str, Any]]:
    raw = os.getenv("SAAS_PLANS", "").strip()
    if raw:
        try:
            plans = json.loads(raw)
            if isinstance(plans, list) and plans:
                return plans
        except json.JSONDecodeError as exc:
            raise ValueError("SAAS_PLANS must be a JSON array") from exc

    return [
        {
            "code": "free",
            "name": "Free",
            "description": "เริ่มต้นใช้งานแพลตฟอร์มและ API พื้นฐาน",
            "price_cents": 0,
            "currency": "thb",
            "interval": "month",
            "api_calls_per_month": 1000,
            "features": ["basic_search", "basic_rag", "api_access"],
            "stripe_price_id": STRIPE_FREE_PRICE_ID,
            "sort_order": 0,
        },
        {
            "code": "pro",
            "name": "Pro",
            "description": "สำหรับทีมที่ต้องการขีดจำกัด API และ_workflow ที่ก้าวหน้าขึ้น",
            "price_cents": 29000,
            "currency": "thb",
            "interval": "month",
            "api_calls_per_month": 100000,
            "features": ["basic_search", "advanced_search", "rag", "api_access", "workflows", "usage_analytics"],
            "stripe_price_id": STRIPE_PRO_PRICE_ID,
            "sort_order": 10,
        },
        {
            "code": "enterprise",
            "name": "Enterprise",
            "description": "แผนสำหรับองค์กร พร้อมการผสานรวมและการสนับสนุนแบบเฉพาะ",
            "price_cents": 99000,
            "currency": "thb",
            "interval": "month",
            "api_calls_per_month": 1000000,
            "features": ["everything_in_pro", "custom_integrations", "sso", "audit_logs", "dedicated_support"],
            "stripe_price_id": STRIPE_ENTERPRISE_PRICE_ID,
            "sort_order": 20,
        },
    ]


MEMBERSHIP_PLANS = _configured_plans()


def validate_production_config() -> None:
    errors: list[str] = []
    if not IS_PRODUCTION:
        return

    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "development-only-change-me-1234567890abcdef":
        errors.append("JWT_SECRET_KEY must be set in production")
    if not CSRF_SECRET_KEY or CSRF_SECRET_KEY == "development-only-change-me-1234567890abcdef":
        errors.append("CSRF_SECRET_KEY must be set in production")
    if not API_KEY_HMAC_SECRET or API_KEY_HMAC_SECRET == "development-only-change-me-1234567890abcdef":
        errors.append("API_KEY_HMAC_SECRET must be set in production")
    if not PROFILE_SECRET_KEY or PROFILE_SECRET_KEY == "development-only-change-me-1234567890abcdef":
        errors.append("PROFILE_SECRET_KEY must be set in production")
    if not STRIPE_SECRET_KEY:
        errors.append("STRIPE_SECRET_KEY must be set in production")
    if not STRIPE_WEBHOOK_SECRET:
        errors.append("STRIPE_WEBHOOK_SECRET must be set in production")
    if not COOKIE_SECURE:
        errors.append("COOKIE_SECURE must be true in production")
    if not ADMIN_EMAILS:
        errors.append("ADMIN_EMAILS must contain at least one administrator")
    if any(origin == "*" for origin in ALLOWED_ORIGINS):
        errors.append("Wildcard CORS origins are not allowed with credentials")

    paid_plans = [plan for plan in MEMBERSHIP_PLANS if int(plan.get("price_cents", 0)) > 0]
    if paid_plans and not all(plan.get("stripe_price_id") for plan in paid_plans):
        errors.append("Every paid plan requires a STRIPE_*_PRICE_ID or SAAS_PLANS price ID")

    if errors:
        raise RuntimeError("Production config validation failed: " + "; ".join(errors))

    if LLM_OFFLINE_FALLBACK and not (OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY):
        logging.getLogger(__name__).warning(
            "No cloud LLM credential is configured; chat and RAG answers will be served by "
            "the deterministic offline responder unless a local Ollama runtime is reachable. "
            "Set OPENAI_API_KEY, ANTHROPIC_API_KEY or GOOGLE_API_KEY to enable real generation."
        )

    logging.getLogger(__name__).info("Production configuration validated")
