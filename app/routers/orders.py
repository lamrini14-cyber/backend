import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.orders import OrderCreateRequest, OrderCreateResponse
from app.services import orders as orders_svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post("/orders", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    body: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    forwarded_for = request.headers.get("x-forwarded-for")
    client_host = request.client.host if request.client else None

    try:
        order = await orders_svc.create_order(db, body, forwarded_for, client_host)
    except ValueError as exc:
        code = str(exc)
        messages = {
            "INVALID_PHONE": "Numéro de téléphone invalide. Utilisez le format 07XXXXXXXX.",
            "HONEYPOT_TRIGGERED": "Requête invalide.",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": code, "message": messages.get(code, str(exc))},
        )
    except PermissionError as exc:
        code = str(exc)
        messages = {
            "IP_NOT_ALLOWED": "Commandes disponibles au Sénégal uniquement.",
            "VPN_DETECTED": "Connexion non autorisée. Désactivez le VPN et réessayez.",
        }
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": code, "message": messages.get(code, str(exc))},
        )
    except LookupError as exc:
        code = str(exc)
        messages = {
            "RATE_LIMIT": "Trop de commandes avec ce numéro. Réessayez demain.",
        }
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": code, "message": messages.get(code, str(exc))},
        )
    except Exception as exc:
        logger.exception("Unexpected error creating order: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "SERVER_ERROR", "message": "Erreur interne. Réessayez."},
        )

    return OrderCreateResponse(
        order_id=str(order.id),
        order_number=order.order_number,
        customer_name=order.customer_name,
        total_fcfa=order.total_fcfa,
        tier_base_fcfa=order.tier_base_fcfa,
        upsell_accepted=order.upsell_accepted,
    )
