import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def check_ip(ip: str) -> tuple[bool, dict]:
    """
    Check IP against MaxMind GeoIP2 Insights.
    Returns (is_allowed, metadata_dict).
    Falls back to allowed=True if MaxMind is not configured.
    """
    settings = get_settings()

    if not settings.MAXMIND_ACCOUNT_ID or not settings.MAXMIND_LICENSE_KEY:
        logger.warning("MaxMind not configured — allowing all IPs")
        return True, {"country": "XX", "note": "maxmind_not_configured"}

    if ip in ("127.0.0.1", "::1"):
        return True, {"country": "XX", "note": "localhost"}

    url = f"https://geoip.maxmind.com/geoip/v2.1/insights/{ip}"
    auth = (str(settings.MAXMIND_ACCOUNT_ID), settings.MAXMIND_LICENSE_KEY)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, auth=auth)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("MaxMind request failed: %s", exc)
        if settings.MAXMIND_STRICT_MODE:
            return False, {"error": str(exc), "blocked_reasons": ["MAXMIND_ERROR"]}
        return True, {"error": str(exc), "note": "maxmind_error_fallback_allowed"}

    country = data.get("country", {}).get("iso_code", "")
    traits = data.get("traits", {})

    blocked_reasons: list[str] = []

    if country != "SN":
        blocked_reasons.append("COUNTRY_NOT_SN")

    if traits.get("is_anonymous_vpn") or traits.get("is_hosting_provider"):
        blocked_reasons.append("VPN_OR_HOSTING")

    if traits.get("is_tor_exit_node"):
        blocked_reasons.append("TOR")

    meta = {
        "country": country,
        "traits": traits,
        "blocked_reasons": blocked_reasons,
    }

    return len(blocked_reasons) == 0, meta


def get_client_ip(forwarded_for: Optional[str], client_host: Optional[str]) -> str:
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return client_host or "127.0.0.1"
