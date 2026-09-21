from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_CORS_ORIGINS: str = "https://sunuyaram.shop,https://www.sunuyaram.shop,http://localhost:3000"
    API_BASE_URL: str = "https://api.namabeauty.shop"

    DATABASE_URL: str = ""

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL or "postgres://sunuyaram:sunuyaram@sunuyaram_sunuyaram:5432/sunuyaram?sslmode=disable"

    GOOGLE_SHEETS_WEBHOOK_URL: Optional[str] = None

    MAXMIND_ACCOUNT_ID: Optional[int] = None
    MAXMIND_LICENSE_KEY: Optional[str] = None
    MAXMIND_STRICT_MODE: bool = False

    PHONE_WHITELIST: str = "0550000000,0781234555"

    META_PIXEL_ID: Optional[str] = None
    META_CAPI_ACCESS_TOKEN: Optional[str] = None
    META_TEST_EVENT_CODE: Optional[str] = None

    TIKTOK_PIXEL_ID: Optional[str] = None
    TIKTOK_ACCESS_TOKEN: Optional[str] = None
    TIKTOK_TEST_EVENT_CODE: Optional[str] = None

    SNAP_PIXEL_ID: Optional[str] = None
    SNAP_CAPI_TOKEN: Optional[str] = None

    ORDER_RATE_LIMIT_PER_PHONE_24H: int = 3

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.APP_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def phone_whitelist_set(self) -> set[str]:
        return {p.strip() for p in self.PHONE_WHITELIST.split(",") if p.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
