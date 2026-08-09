import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.utils.hash_pii import sha256_hex
from app.utils.phone import to_tiktok_phone

logger = logging.getLogger(__name__)

TIKTOK_EVENTS_URL = "https://business-api.tiktok.com/open_api/v1.3/event/track/"


async def send_purchase_event(
    *,
    event_id: str,
    order_number: str,
    total_fcfa: int,
    slugs: list[str],
    phone_local: str,
    ip_address: str,
    user_agent: str,
    ttp: Optional[str] = None,
) -> bool:
    settings = get_settings()
    if not settings.TIKTOK_PIXEL_ID or not settings.TIKTOK_ACCESS_TOKEN:
        logger.warning("TikTok CAPI not configured — skipping")
        return False

    phone_hash = sha256_hex(to_tiktok_phone(phone_local))
    order_hash = sha256_hex(order_number)

    user: dict[str, Any] = {
        "phone_number": phone_hash,
        "external_id": order_hash,
        "ip": ip_address,
        "user_agent": user_agent,
    }
    if ttp:
        user["ttp"] = ttp

    payload: dict[str, Any] = {
        "event_source": "web",
        "event_source_id": settings.TIKTOK_PIXEL_ID,
        "data": [
            {
                "event": "CompletePayment",
                "event_time": str(int(time.time())),
                "event_id": event_id,
                "user": user,
                "properties": {
                    "currency": "XOF",
                    "value": total_fcfa,
                    "content_type": "product",
                    "contents": [{"content_id": s, "quantity": 1} for s in slugs],
                },
            }
        ],
    }
    if settings.TIKTOK_TEST_EVENT_CODE:
        payload["test_event_code"] = settings.TIKTOK_TEST_EVENT_CODE

    headers = {
        "Access-Token": settings.TIKTOK_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(TIKTOK_EVENTS_URL, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("TikTok CAPI Purchase sent: %s", event_id)
            return True
    except httpx.HTTPError as exc:
        logger.error("TikTok CAPI error: %s", exc)
        return False
