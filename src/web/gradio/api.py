"""API communication utilities for Gradio UI."""

import logging
import os
from typing import Any, cast

import requests  # type: ignore[import-untyped]

from src.config.constants import (
    SHORT_API_TIMEOUT,
    UI_HEALTH_CHECK_MAX_RETRIES,
    UI_HEALTH_CHECK_RETRY_DELAY,
    UI_STARTUP_MAX_RETRIES,
    UI_STARTUP_RETRY_DELAY,
)

logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = os.getenv("RAGGED_API_URL", "http://localhost:8000")
API_HEALTH = f"{API_BASE_URL}/api/health"
API_QUERY = f"{API_BASE_URL}/api/query"
API_UPLOAD = f"{API_BASE_URL}/api/upload"
API_COLLECTIONS = f"{API_BASE_URL}/api/collections"


def check_api_health(
    max_retries: int = UI_STARTUP_MAX_RETRIES, retry_delay: float = UI_STARTUP_RETRY_DELAY
) -> dict[str, Any]:
    """Check if API is healthy with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries

    Returns:
        API health status dict
    """
    import time

    for attempt in range(max_retries):
        try:
            response = requests.get(API_HEALTH, timeout=SHORT_API_TIMEOUT)
            response.raise_for_status()
            health_data = cast(dict[str, Any], response.json())
            logger.info(f"API health check successful on attempt {attempt + 1}")
            return health_data
        except Exception as e:  # noqa: BLE001 - Retry on any error
            if attempt < max_retries - 1:
                logger.warning(f"API health check failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...", exc_info=True)
                time.sleep(retry_delay)
            else:
                logger.exception(f"API health check failed after {max_retries} attempts")
                return {"status": "unhealthy", "error": str(e)}

    return {"status": "unhealthy", "error": "Max retries exceeded"}


def get_api_status_display() -> str:
    """Get formatted API status for display.

    Returns:
        Formatted markdown string with API status
    """
    health = check_api_health(
        max_retries=UI_HEALTH_CHECK_MAX_RETRIES, retry_delay=UI_HEALTH_CHECK_RETRY_DELAY
    )
    status = health.get("status", "unknown")

    if status == "healthy" or status == "degraded":
        return "**API Status**: ✅ Connected"
    else:
        error = health.get("error", "Unknown error")
        return f"**API Status**: ❌ Unavailable ({error[:50]}...)"


def get_collections() -> list[str]:
    """Get list of available collections.

    Returns:
        List of collection names
    """
    try:
        response = requests.get(API_COLLECTIONS, timeout=SHORT_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return cast(list[str], data.get("collections", ["default"]))
    except Exception:  # noqa: BLE001 - Return default on any error
        return ["default"]
