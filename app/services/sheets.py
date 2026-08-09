import asyncio
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


async def sync_order_to_sheet(payload: dict[str, Any]) -> bool:
    """
    POST order data to Google Sheets webhook.
    Retries up to MAX_RETRIES times. Returns True on success.
    """
    settings = get_settings()
    url = settings.GOOGLE_SHEETS_WEBHOOK_URL

    if not url:
        logger.warning("GOOGLE_SHEETS_WEBHOOK_URL not set — skipping sheet sync")
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info("Sheet sync OK (attempt %d)", attempt)
                return True
        except httpx.HTTPError as exc:
            logger.warning("Sheet sync attempt %d failed: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)

    return False
