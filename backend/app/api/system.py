"""Public system monitoring API.

Deliberately mounted without `require_platform_user` so the status page and
external uptime probes can read stack health without a session.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.app.observability import telemetry_status
from backend.app.services.platform import monitor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/system/status")
async def system_status() -> Dict[str, Any]:
    """Probe every service in the stack and return one report."""
    try:
        report = await monitor.get_platform_report()
    except Exception as exc:
        logger.exception("system status probe failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    report["telemetry"] = telemetry_status()
    return report