from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas.orders import GeoCheckResponse
from app.services.maxmind import check_ip, get_client_ip

router = APIRouter(prefix="/api/v1", tags=["geo"])


@router.get("/geo/check", response_model=GeoCheckResponse)
async def geo_check(request: Request):
    settings = get_settings()
    ip = get_client_ip(
        request.headers.get("x-forwarded-for"),
        request.client.host if request.client else None,
    )
    if not settings.MAXMIND_ACCOUNT_ID or not settings.MAXMIND_LICENSE_KEY:
        return GeoCheckResponse(allowed=True, country="XX")
    allowed, meta = await check_ip(ip)
    return GeoCheckResponse(allowed=True, country=meta.get("country", "XX"))
