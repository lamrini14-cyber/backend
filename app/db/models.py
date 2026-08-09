import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False)
    name_fr = Column(String(128), nullable=False)
    name_wo = Column(String(128), nullable=False)
    unit_display_fcfa = Column(Integer, nullable=False, default=540)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(32), unique=True, nullable=False)
    customer_name = Column(String(256), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    locale = Column(String(2), nullable=False, default="fr")

    tier_count = Column(Integer, nullable=False)
    tier_base_fcfa = Column(Integer, nullable=False)
    upsell_accepted = Column(Boolean, nullable=False, default=False)
    upsell_sku = Column(String(64), nullable=True)
    upsell_price_fcfa = Column(Integer, nullable=True)
    total_fcfa = Column(Integer, nullable=False)

    payment_method = Column(String(16), nullable=False, default="COD")
    status = Column(String(32), nullable=False, default="new")

    ip_address = Column(INET, nullable=True)
    ip_country = Column(String(2), nullable=True)
    maxmind_risk = Column(JSONB, nullable=True)
    is_whitelisted = Column(Boolean, nullable=False, default=False)

    sheet_synced = Column(Boolean, nullable=False, default=False)
    sheet_sync_error = Column(Text, nullable=True)

    event_id = Column(String(64), nullable=True)
    fbp = Column(String(256), nullable=True)
    fbc = Column(String(256), nullable=True)
    ttp = Column(String(256), nullable=True)
    ttclid = Column(String(256), nullable=True)
    sc_click_id = Column(String(256), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_slug = Column(String(64), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    line_type = Column(String(16), nullable=False, default="standard")
    unit_price_fcfa = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
