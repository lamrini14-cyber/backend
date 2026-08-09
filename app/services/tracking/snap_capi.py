import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.utils.hash_pii import sha256_hex
from app.utils.phone import to_e164_senegal

logger = logging.getLogger(__name__)

SNAP_CAPI_URL = "https://tr.snapchat.com/v3/{pixel_id}/events"


async def send_purchase_event(
    *,
    event_id: str,
    total_fcfa: int,
    order_number: str,
    slugs: list[str],
    phone_local: str,
    ip_address: str,
    user_agent: str,
    sc_click_id: Optional[str] = None,
) -> bool:
    settings = get_settings()
    if not settings.SNAP_PIXEL_ID or not settings.SNAP_CAPI_TOKEN:
        logger.warning("Snap CAPI not configured — skipping")
        return False

    phone_hash = sha256_hex(to_e164_senegal(phone_local))

    event: dict[str, Any] = {
        "event_type": "PURCHASE",
        "event_conversion_type": "WEB",
        "timestamp": str(int(time.time() * 1000)),
        "client_dedup_id": event_id,
        "hashed_phone_number": phone_hash,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "price": total_fcfa,
        "currency": "XOF",
        "transaction_id": order_number,
        "item_ids": slugs,
        "number_items": len(slugs),
    }
    if sc_click_id:
        event["click_id"] = sc_click_id

    payload = {"data": [event]}

    headers = {
        "Authorization": f"Bearer {settings.SNAP_CAPI_TOKEN}",
        "Content-Type": "application/json",
    }
    url = SNAP_CAPI_URL.format(pixel_id=settings.SNAP_PIXEL_ID)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("Snap CAPI Purchase sent: %s", event_id)
            return True
    except httpx.HTTPError as exc:
        logger.error("Snap CAPI error: %s", exc)
        return False
