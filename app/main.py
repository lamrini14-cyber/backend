import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import geo, health, orders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from sqlalchemy import text
    from app.db.session import engine
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text(
                "ALTER TABLE orders ALTER COLUMN ip_address TYPE VARCHAR(45)"
            ))
        except Exception:
            pass
    logger.info("Database tables ensured")
    yield


settings = get_settings()

app = FastAPI(
    title="SUNU YARAMA API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(health.router)
app.include_router(geo.router)
app.include_router(orders.router)
