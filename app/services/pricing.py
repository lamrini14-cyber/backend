from typing import Optional

TIER_PRICES: dict[int, int] = {1: 540, 2: 950, 3: 1400}
UNIT_DISPLAY_FCFA = 540
UPSELL_PRICE = 540

VALID_SLUGS = {"nuit-calm", "energie-vit", "confort-digest"}


def compute_total(
    slugs: list[str],
    upsell_slug: Optional[str] = None,
    upsell_accepted: bool = False,
) -> tuple[int, int, int]:
    """
    Returns (tier_base_fcfa, total_fcfa, tier_count).
    Upsell adds 540 FCFA on top of tier if accepted and valid.
    """
    unique = list(dict.fromkeys(s for s in slugs if s in VALID_SLUGS))
    tier_count = len(unique)
    if tier_count == 0 or tier_count > 3:
        raise ValueError(f"Invalid number of unique SKUs: {tier_count}")

    tier_base = TIER_PRICES[tier_count]
    total = tier_base

    if upsell_accepted and upsell_slug:
        if upsell_slug not in VALID_SLUGS:
            raise ValueError(f"Invalid upsell slug: {upsell_slug}")
        if upsell_slug in unique:
            raise ValueError("Upsell SKU already in cart")
        if tier_count >= 3:
            raise ValueError("Cannot upsell when cart already has 3 unique products")
        total += UPSELL_PRICE

    return tier_base, total, tier_count


def validate_slugs(slugs: list[str]) -> None:
    for slug in slugs:
        if slug not in VALID_SLUGS:
            raise ValueError(f"Unknown product slug: {slug}")
