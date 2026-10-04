"""OpenTelemetry wiring for Grafana Cloud (or any OTLP endpoint).

Tracing stays off until an OTLP endpoint is configured, so local development and
tests are unaffected. The OTel SDK reads `OTEL_EXPORTER_OTLP_ENDPOINT` and
`OTEL_EXPORTER_OTLP_HEADERS` on its own; this module only adds resource
attributes and the auto-instrumentation for FastAPI, SQLAlchemy and httpx.
"""
import logging
import os
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    ParentBased,
    TraceIdRatioBased,
)

logger = logging.getLogger(__name__)

_STATE: Dict[str, Any] = {"enabled": False, "endpoint": None, "service": None}


def _load_optional():
    """Import the OTLP exporter and instrumentors on demand.

    They live in optional packages so an environment without them (a slim test
    install, for example) still imports this module and simply reports tracing
    as unavailable instead of breaking the whole application.
    """
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    return OTLPSpanExporter, FastAPIInstrumentor, HTTPXClientInstrumentor, SQLAlchemyInstrumentor


def _clean_headers() -> Dict[str, str]:
    """Parse `OTEL_EXPORTER_OTLP_HEADERS`, tolerating quotes from .env files."""
    raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    raw = raw.strip().strip("'").strip('"')
    headers = {}
    for item in raw.split(","):
        key, sep, value = item.partition("=")
        if sep and key.strip():
            headers[key.strip()] = value.strip()
    return headers


def _sampler():
    ratio = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    root = ALWAYS_ON if ratio >= 1.0 else TraceIdRatioBased(ratio)
    return ParentBased(root)


def telemetry_status() -> Dict[str, Any]:
    """Non-sensitive view of the tracing setup, surfaced by the status API."""
    return dict(_STATE)


def configure_telemetry(app=None, engine=None) -> Dict[str, Any]:
    """Install tracing when an OTLP endpoint is configured, then instrument app.

    Pass `app` for a FastAPI service; worker processes call it without one.
    """
    endpoint = (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    service_name = (os.getenv("OTEL_SERVICE_NAME") or "dataair-backend").strip()

    if not endpoint:
        _STATE.update(
            {"enabled": False, "endpoint": None, "service": service_name}
        )
        logger.info("telemetry: no OTEL_EXPORTER_OTLP_ENDPOINT set, tracing disabled")
        return dict(_STATE)

    try:
        (
            OTLPSpanExporter,
            FastAPIInstrumentor,
            HTTPXClientInstrumentor,
            SQLAlchemyInstrumentor,
        ) = _load_optional()
    except ImportError as exc:
        _STATE.update(
            {"enabled": False, "endpoint": None, "service": service_name}
        )
        logger.warning("telemetry: OTLP packages missing, tracing disabled (%s)", exc)
        return dict(_STATE)

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "dataair"),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            "deployment.environment.name": os.getenv("APP_ENV", "development"),
        }
    )
    provider = TracerProvider(resource=resource, sampler=_sampler())

    headers = _clean_headers()
    exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces", headers=headers)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    if engine is not None:
        # instrumentation 0.42b0 rejects an AsyncEngine directly; the sync engine
        # underneath is where the query events fire.
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    _STATE.update(
        {
            "enabled": True,
            "endpoint": endpoint.split("://", 1)[-1].split("/")[0],
            "service": service_name,
        }
    )
    logger.info(
        "telemetry: tracing enabled -> %s (service=%s, auth=%s)",
        _STATE["endpoint"],
        service_name,
        "basic" if headers else "none",
    )
    return dict(_STATE)


def shutdown_telemetry(timeout_millis: int = 5000) -> None:
    """Flush pending spans so a restart does not drop the last batch."""
    provider = trace.get_tracer_provider()
    shutdown = getattr(provider, "shutdown", None)
    if shutdown is None:
        return
    try:
        shutdown(timeout_millis=timeout_millis)
    except Exception:  # pragma: no cover - best effort on shutdown
        logger.debug("telemetry: shutdown flush failed", exc_info=True)


def get_tracer(name: Optional[str] = None):
    """Tracer for manual spans; inert until configure_telemetry runs."""
    return trace.get_tracer(name or "dataair")