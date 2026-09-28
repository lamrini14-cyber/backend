from typing import Optional

TIER_PRICES: dict[int, int] = {1: 23000, 2: 43000, 3: 56800}
UNIT_DISPLAY_FCFA = 23000
UPSELL_PRICE = 23000

VALID_SLUGS = {"nuit-calm", "energie-vit", "confort-digest"}

PRODUCT_NAMES_FR: dict[str, str] = {
    "nuit-calm": "NuitCalm — Sommeil & Sérénité",
    "energie-vit": "ÉnergieVit — Énergie & Vitalité",
    "confort-digest": "ConfortDigest — Confort Digestif",
}

PRODUCT_SKUS: dict[str, str] = {
    "nuit-calm": "SY-NC-001",
    "energie-vit": "SY-EV-002",
    "confort-digest": "SY-CD-003",
}


def compute_total(
    slugs: list[str],
    upsell_slug: Optional[str] = None,
    upsell_accepted: bool = False,
) -> tuple[int, int, int]:
    """
    Returns (tier_base_fcfa, total_fcfa, tier_count).
    Upsell adds 23000 FCFA on top of tier if accepted and valid.
    """
    valid_slugs_list = [s for s in slugs if s in VALID_SLUGS]
    total_items = len(valid_slugs_list)
    if total_items == 0:
        raise ValueError("Cart cannot be empty")

    bundles_of_3 = total_items // 3
    remainder = total_items % 3
    
    tier_base = (bundles_of_3 * TIER_PRICES[3]) + (TIER_PRICES.get(remainder, 0) if remainder > 0 else 0)
    total = tier_base

    if upsell_accepted and upsell_slug:
        if upsell_slug not in VALID_SLUGS:
            raise ValueError(f"Invalid upsell slug: {upsell_slug}")
        total += UPSELL_PRICE

    return tier_base, total, total_items


def validate_slugs(slugs: list[str]) -> None:
    for slug in slugs:
        if slug not in VALID_SLUGS:
            raise ValueError(f"Unknown product slug: {slug}")
