from typing import Optional
from pydantic import BaseModel, field_validator


class OrderItemIn(BaseModel):
    slug: str
    quantity: int = 1


class TrackingIn(BaseModel):
    event_id: Optional[str] = None
    fbp: Optional[str] = None
    fbc: Optional[str] = None
    ttp: Optional[str] = None
    ttclid: Optional[str] = None
    sc_click_id: Optional[str] = None
    user_agent: Optional[str] = None
    page_url: Optional[str] = None


class OrderCreateRequest(BaseModel):
    customer_name: str
    phone: str
    locale: str = "fr"
    items: list[OrderItemIn]
    upsell_accepted: bool = False
    upsell_slug: Optional[str] = None
    tracking: Optional[TrackingIn] = None
    honeypot: Optional[str] = None

    @field_validator("customer_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("customer_name is required")
        return v.strip()

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Cart cannot be empty")
        return v


class OrderCreateResponse(BaseModel):
    order_id: str
    order_number: str
    customer_name: str
    total_fcfa: int
    tier_base_fcfa: int
    upsell_accepted: bool


class GeoCheckResponse(BaseModel):
    allowed: bool
    country: str
