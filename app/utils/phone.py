import re

SENEGAL_PHONE_RE = re.compile(r"^0(7[05678]|33)\d{7}$")

VALID_PREFIXES = ["070", "075", "076", "077", "078", "033"]


def validate_senegal_phone(phone: str) -> bool:
    """Return True if phone matches Senegal mobile format (0XXXXXXXXX, 10 digits)."""
    return bool(SENEGAL_PHONE_RE.match(phone))


def normalize_phone(phone: str) -> str:
    """Strip whitespace and ensure 10-digit local format."""
    return phone.strip().replace(" ", "").replace("-", "")


def to_e164_senegal(local: str) -> str:
    """Convert 0771234567 → +221771234567"""
    local = normalize_phone(local)
    digits = local.lstrip("0")
    return f"+221{digits}"


def to_meta_phone(local: str) -> str:
    """Meta CAPI: E.164 digits without '+' → 221771234567"""
    return to_e164_senegal(local).lstrip("+")


def to_tiktok_phone(local: str) -> str:
    """TikTok CAPI: E.164 with '+' → +221771234567"""
    return to_e164_senegal(local)
