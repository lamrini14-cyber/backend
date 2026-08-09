import hashlib


def sha256_hex(value: str) -> str:
    """SHA-256 hex digest of a lowercase-stripped string."""
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def hash_name_part(name: str) -> str:
    """Hash a single name part (first or last) per Meta/TikTok CAPI spec."""
    return sha256_hex(name)


def split_name(full_name: str) -> tuple[str, str]:
    """Split 'Fatou Diop' → ('fatou', 'diop')."""
    parts = full_name.strip().split(None, 1)
    first = parts[0].lower() if parts else ""
    last = parts[1].lower() if len(parts) > 1 else ""
    return first, last
