import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.utils.hash_pii import sha256_hex, hash_name_part, split_name
from app.utils.phone import to_meta_phone

logger = logging.getLogger(__name__)

META_CAPI_URL = "https://graph.facebook.com/v19.0/{pixel_id}/events"


async def send_purchase_event(
    *,
    event_id: str,
    order_number: str,
    total_fcfa: int,
    slugs: list[str],
    customer_name: str,
    phone_local: str,
    ip_address: str,
    user_agent: str,
    fbp: Optional[str] = None,
    fbc: Optional[str] = None,
    page_url: Optional[str] = None,
) -> bool:
    settings = get_settings()
    if not settings.META_PIXEL_ID or not settings.META_CAPI_ACCESS_TOKEN:
        logger.warning("Meta CAPI not configured — skipping")
        return False

    first, last = split_name(customer_name)
    phone_hash = sha256_hex(to_meta_phone(phone_local))

    user_data: dict[str, Any] = {
        "ph": [phone_hash],
        "client_ip_address": ip_address,
        "client_user_agent": user_agent,
    }
    if first:
        user_data["fn"] = [hash_name_part(first)]
    if last:
        user_data["ln"] = [hash_name_part(last)]
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc

    event: dict[str, Any] = {
        "event_name": "Purchase",
        "event_time": int(time.time()),
        "event_id": event_id,
        "action_source": "website",
        "user_data": user_data,
        "custom_data": {
            "currency": "XOF",
            "value": total_fcfa,
            "content_ids": slugs,
            "content_type": "product",
            "order_id": order_number,
            "num_items": len(slugs),
        },
    }
    if page_url:
        event["event_source_url"] = page_url

    payload: dict[str, Any] = {
        "data": [event],
        "access_token": settings.META_CAPI_ACCESS_TOKEN,
    }
    if settings.META_TEST_EVENT_CODE:
        payload["test_event_code"] = settings.META_TEST_EVENT_CODE

    url = META_CAPI_URL.format(pixel_id=settings.META_PIXEL_ID)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Meta CAPI Purchase sent: %s", event_id)
            return True
    except httpx.HTTPError as exc:
        logger.error("Meta CAPI error: %s", exc)
        return False
