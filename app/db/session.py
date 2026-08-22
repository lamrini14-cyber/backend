from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


def _make_async_url(url: str) -> str:
    """Convert postgres:// or postgresql:// to postgresql+asyncpg://
    and strip sslmode param which asyncpg doesn't support."""
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg does not accept sslmode as a query param
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params.pop("sslmode", None)
    cleaned_query = urlencode(params, doseq=True)
    url = urlunparse(parsed._replace(query=cleaned_query))
    return url


settings = get_settings()
async_url = _make_async_url(settings.database_url)

engine = create_async_engine(
    async_url,
    echo=settings.APP_ENV == "development",
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
