import logging
import subprocess
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import geo, health, orders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_DELAY = 3


def run_alembic_upgrade() -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Running Alembic migrations (attempt %d/%d)...", attempt, MAX_RETRIES)
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Alembic migrations complete")
            return
        logger.warning("Alembic attempt %d failed: %s", attempt, result.stderr)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Alembic upgrade head failed after {MAX_RETRIES} attempts:\n{result.stderr}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_alembic_upgrade()
    yield


settings = get_settings()

app = FastAPI(
    title="SUNU YARAMA API",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
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
