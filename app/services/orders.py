import asyncio
import logging
import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Order, OrderItem
from app.schemas.orders import OrderCreateRequest
from app.services import pricing as pricing_svc
from app.services import sheets as sheets_svc
from app.services.maxmind import check_ip, get_client_ip
from app.services.tracking import meta_capi, snap_capi, tiktok_capi
from app.utils.phone import normalize_phone, validate_senegal_phone

logger = logging.getLogger(__name__)


def _generate_order_number() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SY-{today}-{suffix}"


async def _check_rate_limit(db: AsyncSession, phone: str) -> bool:
    settings = get_settings()
    limit = settings.ORDER_RATE_LIMIT_PER_PHONE_24H
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await db.execute(
        select(func.count(Order.id)).where(
            Order.phone == phone,
            Order.created_at >= since,
        )
    )
    count = result.scalar_one()
    return count < limit


async def create_order(
    db: AsyncSession,
    request: OrderCreateRequest,
    forwarded_for: str | None,
    client_host: str | None,
) -> Order:
    settings = get_settings()

    if request.honeypot:
        raise ValueError("HONEYPOT_TRIGGERED")

    phone = normalize_phone(request.phone)
    if not validate_senegal_phone(phone):
        raise ValueError("INVALID_PHONE")

    is_whitelisted = phone in settings.phone_whitelist_set
    ip_address = get_client_ip(forwarded_for, client_host)

    maxmind_risk: dict = {}
    ip_country = "XX"

    if not is_whitelisted and settings.MAXMIND_ACCOUNT_ID and settings.MAXMIND_LICENSE_KEY:
        try:
            allowed, maxmind_risk = await check_ip(ip_address)
            ip_country = maxmind_risk.get("country", "XX")
            if not allowed:
                blocked_reasons = maxmind_risk.get("blocked_reasons", [])
                if "VPN_OR_HOSTING" in blocked_reasons or "TOR" in blocked_reasons:
                    raise PermissionError("VPN_DETECTED")
        except PermissionError:
            raise
        except Exception as exc:
            logger.warning("MaxMind check failed, allowing order: %s", exc)
            maxmind_risk = {"error": str(exc), "note": "check_failed_allowed"}
    else:
        maxmind_risk = {"note": "whitelisted" if is_whitelisted else "maxmind_not_configured"}

    if not await _check_rate_limit(db, phone):
        raise LookupError("RATE_LIMIT")

    slugs = [item.slug for item in request.items for _ in range(item.quantity)]
    pricing_svc.validate_slugs(slugs)

    upsell_accepted = request.upsell_accepted and bool(request.upsell_slug)
    tier_base, total_fcfa, tier_count = pricing_svc.compute_total(
        slugs,
        upsell_slug=request.upsell_slug if upsell_accepted else None,
        upsell_accepted=upsell_accepted,
    )

    order_number = _generate_order_number()
    tracking = request.tracking or {}
    tracking_dict = tracking.model_dump() if hasattr(tracking, "model_dump") else {}

    order = Order(
        order_number=order_number,
        customer_name=request.customer_name,
        phone=phone,
        locale=request.locale,
        tier_count=tier_count,
        tier_base_fcfa=tier_base,
        upsell_accepted=upsell_accepted,
        upsell_sku=request.upsell_slug if upsell_accepted else None,
        upsell_price_fcfa=pricing_svc.UPSELL_PRICE if upsell_accepted else None,
        total_fcfa=total_fcfa,
        ip_address=ip_address,
        ip_country=ip_country,
        maxmind_risk=maxmind_risk,
        is_whitelisted=is_whitelisted,
        event_id=tracking_dict.get("event_id"),
        fbp=tracking_dict.get("fbp"),
        fbc=tracking_dict.get("fbc"),
        ttp=tracking_dict.get("ttp"),
        ttclid=tracking_dict.get("ttclid"),
        sc_click_id=tracking_dict.get("sc_click_id"),
        user_agent=tracking_dict.get("user_agent"),
    )

    unique_slugs = list(dict.fromkeys(s for s in slugs if s in pricing_svc.VALID_SLUGS))
    tier_price_per_unit = tier_base // max(len(unique_slugs), 1)

    for slug in unique_slugs:
        order.items.append(
            OrderItem(
                product_slug=slug,
                quantity=1,
                line_type="standard",
                unit_price_fcfa=tier_price_per_unit,
            )
        )

    if upsell_accepted and request.upsell_slug:
        order.items.append(
            OrderItem(
                product_slug=request.upsell_slug,
                quantity=1,
                line_type="upsell",
                unit_price_fcfa=pricing_svc.UPSELL_PRICE,
            )
        )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    all_slugs = unique_slugs + ([request.upsell_slug] if upsell_accepted and request.upsell_slug else [])
    asyncio.create_task(_post_order_tasks(order, all_slugs, tracking_dict, ip_address))

    return order


async def _post_order_tasks(
    order: Order,
    all_slugs: list[str],
    tracking: dict,
    ip_address: str,
) -> None:
    sheet_payload = {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "created_at": order.created_at.isoformat(),
        "customer_name": order.customer_name,
        "phone": order.phone,
        "locale": order.locale,
        "tier_count": order.tier_count,
        "tier_base_fcfa": order.tier_base_fcfa,
        "upsell_accepted": order.upsell_accepted,
        "upsell_sku": order.upsell_sku,
        "upsell_price_fcfa": order.upsell_price_fcfa,
        "total_fcfa": order.total_fcfa,
        "items": [{"slug": i.product_slug, "qty": i.quantity, "line_type": i.line_type} for i in order.items],
        "payment_method": "COD",
        "ip_country": order.ip_country,
        "is_whitelisted": order.is_whitelisted,
        "event_id": order.event_id,
        "status": order.status,
    }

    capi_kwargs = dict(
        event_id=order.event_id or str(order.id),
        order_number=order.order_number,
        total_fcfa=order.total_fcfa,
        slugs=all_slugs,
        customer_name=order.customer_name,
        phone_local=order.phone,
        ip_address=ip_address,
        user_agent=order.user_agent or "",
        fbp=order.fbp,
        fbc=order.fbc,
        page_url=tracking.get("page_url"),
    )

    await asyncio.gather(
        sheets_svc.sync_order_to_sheet(sheet_payload),
        meta_capi.send_purchase_event(**capi_kwargs),
        tiktok_capi.send_purchase_event(
            event_id=order.event_id or str(order.id),
            order_number=order.order_number,
            total_fcfa=order.total_fcfa,
            slugs=all_slugs,
            phone_local=order.phone,
            ip_address=ip_address,
            user_agent=order.user_agent or "",
            ttp=order.ttp,
        ),
        snap_capi.send_purchase_event(
            event_id=order.event_id or str(order.id),
            total_fcfa=order.total_fcfa,
            order_number=order.order_number,
            slugs=all_slugs,
            phone_local=order.phone,
            ip_address=ip_address,
            user_agent=order.user_agent or "",
            sc_click_id=order.sc_click_id,
        ),
        return_exceptions=True,
    )
