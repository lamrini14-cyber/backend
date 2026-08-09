"""initial schema + seed products

Revision ID: 0001
Revises: 
Create Date: 2026-07-12

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name_fr", sa.String(128), nullable=False),
        sa.Column("name_wo", sa.String(128), nullable=False),
        sa.Column("unit_display_fcfa", sa.Integer, nullable=False, server_default="540"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_number", sa.String(32), unique=True, nullable=False),
        sa.Column("customer_name", sa.String(256), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("locale", sa.String(2), nullable=False, server_default="fr"),
        sa.Column("tier_count", sa.Integer, nullable=False),
        sa.Column("tier_base_fcfa", sa.Integer, nullable=False),
        sa.Column("upsell_accepted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("upsell_sku", sa.String(64), nullable=True),
        sa.Column("upsell_price_fcfa", sa.Integer, nullable=True),
        sa.Column("total_fcfa", sa.Integer, nullable=False),
        sa.Column("payment_method", sa.String(16), nullable=False, server_default="COD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="new"),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("ip_country", sa.String(2), nullable=True),
        sa.Column("maxmind_risk", postgresql.JSONB, nullable=True),
        sa.Column("is_whitelisted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sheet_synced", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sheet_sync_error", sa.Text, nullable=True),
        sa.Column("event_id", sa.String(64), nullable=True),
        sa.Column("fbp", sa.String(256), nullable=True),
        sa.Column("fbc", sa.String(256), nullable=True),
        sa.Column("ttp", sa.String(256), nullable=True),
        sa.Column("ttclid", sa.String(256), nullable=True),
        sa.Column("sc_click_id", sa.String(256), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_orders_phone", "orders", ["phone"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_slug", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("line_type", sa.String(16), nullable=False, server_default="standard"),
        sa.Column("unit_price_fcfa", sa.Integer, nullable=False),
    )

    now = datetime.now(timezone.utc).isoformat()
    op.execute(
        f"""
        INSERT INTO products (id, slug, name_fr, name_wo, unit_display_fcfa, active, created_at)
        VALUES
          ('{uuid.uuid4()}', 'nuit-calm',      'NuitCalm',      'Sopi',    540, true, '{now}'),
          ('{uuid.uuid4()}', 'energie-vit',    'ÉnergieVit',    'Kalaite', 540, true, '{now}'),
          ('{uuid.uuid4()}', 'confort-digest', 'ConfortDigest', 'Gox',     540, true, '{now}')
        """
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_phone", table_name="orders")
    op.drop_table("orders")
    op.drop_table("products")
