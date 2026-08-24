"""Astronomical Utility Functions.

Provides:
- High-precision DMS (Degrees, Minutes, Seconds) formatting and conversion
- Intra-sign (0° - 30°) calculation and zodiac sign resolution
- Nakshatra subdivision calculation (Nakshatra 1-27, Pada 1-4, and elapsed balance fraction)
"""

import math
from typing import Any

from core.constants import (
    NAKSHATRA_ARC_DEG,
    NAKSHATRAS,
    PADA_ARC_DEG,
    ZODIAC_SIGNS,
    PlanetEnum,
)


def normalize_degrees(degrees: float) -> float:
    """Normalizes an angle to the range [0.0, 360.0)."""
    return degrees % 360.0


def decimal_to_dms(decimal_deg: float) -> tuple[int, int, float, str]:
    """Converts decimal degrees into integer degrees, integer arcminutes, float arcseconds, and formatted string.

    Args:
        decimal_deg: Angle in decimal degrees (e.g. 124.5678).

    Returns:
        Tuple of (degrees, arcminutes, arcseconds, formatted_string).
        Example: (124, 34, 4.08, "124° 34' 04.08\\"")
    """
    is_negative = decimal_deg < 0
    abs_deg = abs(decimal_deg)

    d = int(math.floor(abs_deg))
    rem_min = (abs_deg - d) * 60.0
    m = int(math.floor(rem_min))
    s = (rem_min - m) * 60.0

    # Handle edge case where rounding seconds pushes minutes to 60
    if round(s, 4) >= 60.0:
        s = 0.0
        m += 1
        if m >= 60:
            m = 0
            d += 1

    prefix = "-" if is_negative else ""
    formatted = f'{prefix}{d}° {m:02d}\' {s:05.2f}"'
    final_deg = -d if is_negative else d

    return final_deg, m, round(s, 4), formatted


def get_sign_placement(longitude: float) -> dict[str, Any]:
    """Determines zodiac sign placement and intra-sign degrees (0° - 30°) from absolute longitude.

    Args:
        longitude: Sidereal longitude in degrees (0.0 to 360.0).

    Returns:
        Dictionary containing sign id, sanskrit name, english name, lord,
        intra-sign degree, and intra-sign DMS.
    """
    lon_norm = normalize_degrees(longitude)
    sign_idx = int(lon_norm // 30.0) + 1
    intra_sign_deg = lon_norm % 30.0

    sign_info = ZODIAC_SIGNS[sign_idx]
    deg, minutes, seconds, dms_str = decimal_to_dms(intra_sign_deg)

    return {
        "id": sign_info["id"],
        "sanskrit_name": sign_info["sanskrit_name"],
        "english_name": sign_info["english_name"],
        "lord": sign_info["lord"],
        "element": sign_info["element"],
        "modality": sign_info["modality"],
        "intra_sign_degree": intra_sign_deg,
        "dms": {
            "degrees": deg,
            "minutes": minutes,
            "seconds": seconds,
            "formatted": dms_str,
        },
    }


def get_nakshatra_placement(longitude: float) -> dict[str, Any]:
    """Calculates Nakshatra index (1-27), Pada (1-4), elapsed arc, and elapsed fraction.

    Args:
        longitude: Sidereal longitude in degrees (0.0 to 360.0).

    Returns:
        Dictionary containing nakshatra id, sanskrit name, lord, dasha years,
        pada (1-4), elapsed degrees, and elapsed fraction (0.0 - 1.0) for Vimshottari dasha.
    """
    lon_norm = normalize_degrees(longitude)
    nak_idx = int(lon_norm // NAKSHATRA_ARC_DEG) + 1
    if nak_idx > 27:
        nak_idx = 27

    nak_info = NAKSHATRAS[nak_idx]
    elapsed_in_nak = lon_norm - ((nak_idx - 1) * NAKSHATRA_ARC_DEG)
    if elapsed_in_nak < 0:
        elapsed_in_nak = 0.0

    pada = int(elapsed_in_nak // PADA_ARC_DEG) + 1
    if pada > 4:
        pada = 4

    elapsed_fraction = elapsed_in_nak / NAKSHATRA_ARC_DEG
    pada_start = (nak_idx - 1) * NAKSHATRA_ARC_DEG + (pada - 1) * PADA_ARC_DEG
    pada_end = pada_start + PADA_ARC_DEG

    return {
        "id": nak_info["id"],
        "sanskrit_name": nak_info["sanskrit_name"],
        "lord": nak_info["lord"],
        "dasha_years": nak_info["dasha_years"],
        "pada": pada,
        "elapsed_degrees": elapsed_in_nak,
        "elapsed_fraction": elapsed_fraction,
        "pada_start_deg": pada_start,
        "pada_end_deg": pada_end,
    }


def angular_distance(lon1: float, lon2: float) -> float:
    """Computes the shortest angular distance between two longitudes on a 360° circle.

    Args:
        lon1: First longitude in degrees.
        lon2: Second longitude in degrees.

    Returns:
        Shortest distance in degrees in range [0.0, 180.0].
    """
    diff = abs(normalize_degrees(lon1) - normalize_degrees(lon2)) % 360.0
    return 360.0 - diff if diff > 180.0 else diff
