from fastapi import APIRouter, Request

from app.schemas.orders import GeoCheckResponse
from app.services.maxmind import check_ip, get_client_ip

router = APIRouter(prefix="/api/v1", tags=["geo"])


@router.get("/geo/check", response_model=GeoCheckResponse)
async def geo_check(request: Request):
    ip = get_client_ip(
        request.headers.get("x-forwarded-for"),
        request.client.host if request.client else None,
    )
    allowed, meta = await check_ip(ip)
    return GeoCheckResponse(allowed=allowed, country=meta.get("country", "XX"))
