"""Geolocation and Timezone Resolution Subsystem.

Provides:
- Nominatim geocoding with custom User-Agent and timeout handling
- Offline IANA timezone lookup via TimezoneFinder
- DST-aware and timezone-aware conversion from local datetime to UTC using zoneinfo
"""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


class GeoResolver:
    """Handles address geocoding and coordinates to IANA timezone mapping."""

    def __init__(self, user_agent: str = "astrology_engine/1.0", timeout: int = 10) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._geolocator = Nominatim(user_agent=self._user_agent, timeout=self._timeout)
        self._tf = TimezoneFinder()

    def geocode(
        self,
        query: str,
    ) -> tuple[float, float, Optional[str], Optional[str]]:
        """Geocodes an address or city query to (latitude, longitude, city, country).

        Args:
            query: Address, city, or location string.

        Returns:
            Tuple of (latitude, longitude, city_name, country_name).

        Raises:
            ValueError: If the location query cannot be resolved.
            RuntimeError: If geocoding service times out or is unavailable.
        """
        try:
            location = self._geolocator.geocode(query, addressdetails=True)
            if not location:
                raise ValueError(f"Could not resolve coordinates for query: '{query}'")

            raw_address = location.raw.get("address", {})
            city = (
                raw_address.get("city")
                or raw_address.get("town")
                or raw_address.get("village")
                or raw_address.get("county")
                or location.address.split(",")[0]
            )
            country = raw_address.get("country", "")

            return location.latitude, location.longitude, city, country

        except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as err:
            raise RuntimeError(f"Geocoding service error for '{query}': {err}") from err

    def get_timezone_for_coordinates(self, latitude: float, longitude: float) -> str:
        """Resolves the IANA timezone string (e.g. 'Asia/Kolkata') from lat/lon.

        Args:
            latitude: Latitude in decimal degrees (-90.0 to 90.0).
            longitude: Longitude in decimal degrees (-180.0 to 180.0).

        Returns:
            IANA timezone string name.

        Raises:
            ValueError: If timezone cannot be determined for given coordinates.
        """
        tz_name = self._tf.timezone_at(lat=latitude, lng=longitude)
        if not tz_name:
            # Fallback to closest timezone if on border/water
            tz_name = self._tf.closest_timezone_at(lat=latitude, lng=longitude)

        if not tz_name:
            raise ValueError(f"Could not determine IANA timezone for lat={latitude}, lon={longitude}")

        return tz_name


def to_utc_datetime(
    dt_local: datetime,
    timezone_str: str,
) -> datetime:
    """Converts a local datetime (naive or aware) to UTC using Python's zoneinfo.

    Args:
        dt_local: The local datetime of birth.
        timezone_str: IANA timezone string (e.g., 'Asia/Kolkata', 'America/New_York').

    Returns:
        Timezone-aware datetime in UTC (ZoneInfo('UTC')).

    Raises:
        ValueError: If timezone string is invalid.
    """
    try:
        tz = ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid or unrecognized IANA timezone: '{timezone_str}'") from exc

    # If datetime is naive, attach local timezone
    if dt_local.tzinfo is None:
        aware_dt = dt_local.replace(tzinfo=tz)
    else:
        aware_dt = dt_local.astimezone(tz)

    return aware_dt.astimezone(ZoneInfo("UTC"))
