"""Geolocation and Timezone Resolution Subsystem.

Provides:
- Multi-tier resilient geocoding:
  1. Instant offline curated database of major Indian cities, sacred Vedic centers, and global capitals
  2. Open-Meteo Geocoding API (free, cloud-friendly, zero rate limits for web apps, no API key required)
  3. Photon Geocoding API by Komoot (free OSM-based secondary fallback)
  4. Nominatim with custom User-Agent and timeout handling (tertiary fallback)
  5. Direct coordinate input parsing (e.g. "26.9124, 75.7873")
- Offline IANA timezone lookup via TimezoneFinder
- DST-aware and timezone-aware conversion from local datetime to UTC using zoneinfo
"""

from datetime import datetime
import json
import re
from typing import Optional
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


# =============================================================================
# Curated Offline Cities Database (Tier 1 - Instant 0ms Resolution)
# =============================================================================

# Format: key -> (lat, lon, display_city, country, timezone_str)
OFFLINE_CITIES: dict[str, tuple[float, float, str, str, str]] = {
    # Major Indian Metros & State Capitals
    "jaipur": (26.9124, 75.7873, "Jaipur", "India", "Asia/Kolkata"),
    "delhi": (28.6139, 77.2090, "New Delhi", "India", "Asia/Kolkata"),
    "new delhi": (28.6139, 77.2090, "New Delhi", "India", "Asia/Kolkata"),
    "mumbai": (19.0760, 72.8777, "Mumbai", "India", "Asia/Kolkata"),
    "bombay": (19.0760, 72.8777, "Mumbai", "India", "Asia/Kolkata"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru", "India", "Asia/Kolkata"),
    "bangalore": (12.9716, 77.5946, "Bengaluru", "India", "Asia/Kolkata"),
    "kolkata": (22.5726, 88.3639, "Kolkata", "India", "Asia/Kolkata"),
    "calcutta": (22.5726, 88.3639, "Kolkata", "India", "Asia/Kolkata"),
    "chennai": (13.0827, 80.2707, "Chennai", "India", "Asia/Kolkata"),
    "madras": (13.0827, 80.2707, "Chennai", "India", "Asia/Kolkata"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad", "India", "Asia/Kolkata"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad", "India", "Asia/Kolkata"),
    "pune": (18.5204, 73.8567, "Pune", "India", "Asia/Kolkata"),
    "poona": (18.5204, 73.8567, "Pune", "India", "Asia/Kolkata"),
    "surat": (21.1702, 72.8311, "Surat", "India", "Asia/Kolkata"),
    "lucknow": (26.8467, 80.9462, "Lucknow", "India", "Asia/Kolkata"),
    "kanpur": (26.4499, 80.3319, "Kanpur", "India", "Asia/Kolkata"),
    "nagpur": (21.1458, 79.0882, "Nagpur", "India", "Asia/Kolkata"),
    "indore": (22.7196, 75.8577, "Indore", "India", "Asia/Kolkata"),
    "thane": (19.2183, 72.9781, "Thane", "India", "Asia/Kolkata"),
    "bhopal": (23.2599, 77.4126, "Bhopal", "India", "Asia/Kolkata"),
    "visakhapatnam": (17.6868, 83.2185, "Visakhapatnam", "India", "Asia/Kolkata"),
    "vizag": (17.6868, 83.2185, "Visakhapatnam", "India", "Asia/Kolkata"),
    "patna": (25.5941, 85.1376, "Patna", "India", "Asia/Kolkata"),
    "vadodara": (22.3072, 73.1812, "Vadodara", "India", "Asia/Kolkata"),
    "baroda": (22.3072, 73.1812, "Vadodara", "India", "Asia/Kolkata"),
    "ghaziabad": (28.6692, 77.4538, "Ghaziabad", "India", "Asia/Kolkata"),
    "ludhiana": (30.9010, 75.8573, "Ludhiana", "India", "Asia/Kolkata"),
    "agra": (27.1767, 78.0081, "Agra", "India", "Asia/Kolkata"),
    "nashik": (19.9975, 73.7898, "Nashik", "India", "Asia/Kolkata"),
    "faridabad": (28.4089, 77.3178, "Faridabad", "India", "Asia/Kolkata"),
    "meerut": (28.9845, 77.7064, "Meerut", "India", "Asia/Kolkata"),
    "rajkot": (22.3039, 70.8022, "Rajkot", "India", "Asia/Kolkata"),
    "kalyan": (19.2403, 73.1305, "Kalyan", "India", "Asia/Kolkata"),
    "srinagar": (34.0837, 74.7973, "Srinagar", "India", "Asia/Kolkata"),
    "aurangabad": (19.8762, 75.3433, "Aurangabad", "India", "Asia/Kolkata"),
    "chhatrapati sambhajinagar": (19.8762, 75.3433, "Chhatrapati Sambhajinagar", "India", "Asia/Kolkata"),
    "dhanbad": (23.7957, 86.4304, "Dhanbad", "India", "Asia/Kolkata"),
    "amritsar": (31.6340, 74.8723, "Amritsar", "India", "Asia/Kolkata"),
    "navi mumbai": (19.0330, 73.0297, "Navi Mumbai", "India", "Asia/Kolkata"),
    "prayagraj": (25.4358, 81.8463, "Prayagraj", "India", "Asia/Kolkata"),
    "allahabad": (25.4358, 81.8463, "Prayagraj", "India", "Asia/Kolkata"),
    "ranchi": (23.3441, 85.3096, "Ranchi", "India", "Asia/Kolkata"),
    "howrah": (22.5958, 88.2636, "Howrah", "India", "Asia/Kolkata"),
    "coimbatore": (11.0168, 76.9558, "Coimbatore", "India", "Asia/Kolkata"),
    "jabalpur": (23.1815, 79.9864, "Jabalpur", "India", "Asia/Kolkata"),
    "gwalior": (26.2183, 78.1828, "Gwalior", "India", "Asia/Kolkata"),
    "vijayawada": (16.5062, 80.6480, "Vijayawada", "India", "Asia/Kolkata"),
    "jodhpur": (26.2389, 73.0243, "Jodhpur", "India", "Asia/Kolkata"),
    "madurai": (9.9252, 78.1198, "Madurai", "India", "Asia/Kolkata"),
    "raipur": (21.2514, 81.6296, "Raipur", "India", "Asia/Kolkata"),
    "kota": (25.2138, 75.8648, "Kota", "India", "Asia/Kolkata"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh", "India", "Asia/Kolkata"),
    "guwahati": (26.1445, 91.7362, "Guwahati", "India", "Asia/Kolkata"),
    "solapur": (17.6599, 75.9064, "Solapur", "India", "Asia/Kolkata"),
    "hubli": (15.3647, 75.1240, "Hubli", "India", "Asia/Kolkata"),
    "bareilly": (28.3670, 79.4304, "Bareilly", "India", "Asia/Kolkata"),
    "moradabad": (28.8386, 78.7733, "Moradabad", "India", "Asia/Kolkata"),
    "mysuru": (12.2958, 76.6394, "Mysuru", "India", "Asia/Kolkata"),
    "mysore": (12.2958, 76.6394, "Mysuru", "India", "Asia/Kolkata"),
    "gurugram": (28.4595, 77.0266, "Gurugram", "India", "Asia/Kolkata"),
    "gurgaon": (28.4595, 77.0266, "Gurugram", "India", "Asia/Kolkata"),
    "aligarh": (27.8974, 78.0880, "Aligarh", "India", "Asia/Kolkata"),
    "jalandhar": (31.3260, 75.5762, "Jalandhar", "India", "Asia/Kolkata"),
    "tiruchirappalli": (10.7905, 78.7047, "Tiruchirappalli", "India", "Asia/Kolkata"),
    "trichy": (10.7905, 78.7047, "Tiruchirappalli", "India", "Asia/Kolkata"),
    "bhubaneswar": (20.2961, 85.8245, "Bhubaneswar", "India", "Asia/Kolkata"),
    "salem": (11.6643, 78.1460, "Salem", "India", "Asia/Kolkata"),
    "warangal": (17.9689, 79.5941, "Warangal", "India", "Asia/Kolkata"),
    "thiruvananthapuram": (8.5241, 76.9366, "Thiruvananthapuram", "India", "Asia/Kolkata"),
    "trivandrum": (8.5241, 76.9366, "Thiruvananthapuram", "India", "Asia/Kolkata"),
    "dehradun": (30.3165, 78.0322, "Dehradun", "India", "Asia/Kolkata"),
    "shimla": (31.1048, 77.1734, "Shimla", "India", "Asia/Kolkata"),
    "jammu": (32.7266, 74.8570, "Jammu", "India", "Asia/Kolkata"),
    "noida": (28.5355, 77.3910, "Noida", "India", "Asia/Kolkata"),
    "kochi": (9.9312, 76.2673, "Kochi", "India", "Asia/Kolkata"),
    "cochin": (9.9312, 76.2673, "Kochi", "India", "Asia/Kolkata"),
    "mangaluru": (12.9141, 74.8560, "Mangaluru", "India", "Asia/Kolkata"),
    "mangalore": (12.9141, 74.8560, "Mangaluru", "India", "Asia/Kolkata"),
    "udaipur": (24.5854, 73.7125, "Udaipur", "India", "Asia/Kolkata"),
    "ajmer": (26.4499, 74.6399, "Ajmer", "India", "Asia/Kolkata"),
    "bikaner": (28.0229, 73.3119, "Bikaner", "India", "Asia/Kolkata"),

    # Sacred Astrological & Pilgrimage Centers
    "varanasi": (25.3176, 82.9739, "Varanasi", "India", "Asia/Kolkata"),
    "kashi": (25.3176, 82.9739, "Varanasi", "India", "Asia/Kolkata"),
    "banaras": (25.3176, 82.9739, "Varanasi", "India", "Asia/Kolkata"),
    "ujjain": (23.1765, 75.7885, "Ujjain", "India", "Asia/Kolkata"),
    "haridwar": (29.9457, 78.1642, "Haridwar", "India", "Asia/Kolkata"),
    "rishikesh": (30.0869, 78.2676, "Rishikesh", "India", "Asia/Kolkata"),
    "mathura": (27.4924, 77.6737, "Mathura", "India", "Asia/Kolkata"),
    "vrindavan": (27.5806, 77.7006, "Vrindavan", "India", "Asia/Kolkata"),
    "ayodhya": (26.7922, 82.1998, "Ayodhya", "India", "Asia/Kolkata"),
    "tirupati": (13.6288, 79.4192, "Tirupati", "India", "Asia/Kolkata"),
    "puri": (19.8135, 85.8312, "Puri", "India", "Asia/Kolkata"),
    "rameshwaram": (9.2876, 79.3129, "Rameshwaram", "India", "Asia/Kolkata"),
    "somnath": (20.8880, 70.4012, "Somnath", "India", "Asia/Kolkata"),
    "dwarka": (22.2442, 68.9685, "Dwarka", "India", "Asia/Kolkata"),
    "badrinath": (30.7433, 79.4938, "Badrinath", "India", "Asia/Kolkata"),
    "kedarnath": (30.7352, 79.0669, "Kedarnath", "India", "Asia/Kolkata"),
    "gangotri": (30.9947, 78.9398, "Gangotri", "India", "Asia/Kolkata"),
    "yamunotri": (31.0140, 78.4600, "Yamunotri", "India", "Asia/Kolkata"),
    "shirdi": (19.7667, 74.4766, "Shirdi", "India", "Asia/Kolkata"),
    "gaya": (24.7914, 85.0002, "Gaya", "India", "Asia/Kolkata"),
    "kurukshetra": (29.9695, 76.8783, "Kurukshetra", "India", "Asia/Kolkata"),
    "pushkar": (26.4897, 74.5511, "Pushkar", "India", "Asia/Kolkata"),

    # Key Global Metros
    "new york": (40.7128, -74.0060, "New York", "United States", "America/New_York"),
    "nyc": (40.7128, -74.0060, "New York", "United States", "America/New_York"),
    "london": (51.5074, -0.1278, "London", "United Kingdom", "Europe/London"),
    "dubai": (25.2048, 55.2708, "Dubai", "United Arab Emirates", "Asia/Dubai"),
    "singapore": (1.3521, 103.8198, "Singapore", "Singapore", "Asia/Singapore"),
    "toronto": (43.6532, -79.3832, "Toronto", "Canada", "America/Toronto"),
    "san francisco": (37.7749, -122.4194, "San Francisco", "United States", "America/Los_Angeles"),
    "los angeles": (34.0522, -118.2437, "Los Angeles", "United States", "America/Los_Angeles"),
    "chicago": (41.8781, -87.6298, "Chicago", "United States", "America/Chicago"),
    "sydney": (-33.8688, 151.2093, "Sydney", "Australia", "Australia/Sydney"),
    "melbourne": (-37.8136, 144.9631, "Melbourne", "Australia", "Australia/Melbourne"),
    "tokyo": (35.6762, 139.6503, "Tokyo", "Japan", "Asia/Tokyo"),
    "paris": (48.8566, 2.3522, "Paris", "France", "Europe/Paris"),
    "berlin": (52.5200, 13.4050, "Berlin", "Germany", "Europe/Berlin"),
    "bangkok": (13.7563, 100.5018, "Bangkok", "Thailand", "Asia/Bangkok"),
    "kuala lumpur": (3.1390, 101.6869, "Kuala Lumpur", "Malaysia", "Asia/Kuala_Lumpur"),
    "hong kong": (22.3193, 114.1694, "Hong Kong", "Hong Kong", "Asia/Hong_Kong"),
    "kathmandu": (27.7172, 85.3240, "Kathmandu", "Nepal", "Asia/Kathmandu"),
    "colombo": (6.9271, 79.8612, "Colombo", "Sri Lanka", "Asia/Colombo"),
    "dhaka": (23.8103, 90.4125, "Dhaka", "Bangladesh", "Asia/Dhaka"),
    "moscow": (55.7558, 37.6173, "Moscow", "Russia", "Europe/Moscow"),
    "johannesburg": (-26.2041, 28.0473, "Johannesburg", "South Africa", "Africa/Johannesburg"),
    "auckland": (-36.8485, 174.7633, "Auckland", "New Zealand", "Pacific/Auckland"),
}


class GeoResolver:
    """Handles resilient multi-tiered address geocoding and coordinates to IANA timezone mapping."""

    def __init__(self, user_agent: str = "TrinetriAI-VedicStudio/2.0", timeout: int = 10) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._geolocator = Nominatim(user_agent=self._user_agent, timeout=self._timeout)
        self._tf = TimezoneFinder()
        # In-memory cache to avoid redundant lookups
        self._cache: dict[str, tuple[float, float, Optional[str], Optional[str]]] = {}
        self._tz_cache: dict[tuple[float, float], str] = {}

    def _try_parse_coordinates(self, query: str) -> Optional[tuple[float, float, str, str]]:
        """Checks if the user entered raw numeric coordinates (e.g. '26.9124, 75.7873')."""
        parts = re.split(r"[\s,]+", query.strip())
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    return lat, lon, "Custom Coordinates", ""
            except ValueError:
                pass
        return None

    def _query_open_meteo(self, query: str, timeout: float = 5.0) -> Optional[tuple[float, float, str, str, Optional[str]]]:
        """Queries Open-Meteo's free global geocoding API (no API key, cloud-friendly)."""
        clean_q = query.strip()
        search_terms = [clean_q]
        if "," in clean_q:
            search_terms.append(clean_q.split(",")[0].strip())

        for term in search_terms:
            if not term:
                continue
            encoded = urllib.parse.quote(term)
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en&format=json"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self._user_agent, "Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        results = data.get("results")
                        if results and len(results) > 0:
                            r = results[0]
                            lat = float(r["latitude"])
                            lon = float(r["longitude"])
                            city = r.get("name", "")
                            country = r.get("country", "")
                            tz = r.get("timezone")
                            return lat, lon, city, country, tz
            except Exception:
                continue
        return None

    def _query_photon(self, query: str, timeout: float = 5.0) -> Optional[tuple[float, float, str, str, Optional[str]]]:
        """Queries Photon (Komoot OSM-based free geocoding API)."""
        clean_q = query.strip()
        encoded = urllib.parse.quote(clean_q)
        url = f"https://photon.komoot.io/api/?q={encoded}&limit=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self._user_agent, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    features = data.get("features", [])
                    if features:
                        f = features[0]
                        coords = f["geometry"]["coordinates"]
                        lon, lat = float(coords[0]), float(coords[1])
                        props = f.get("properties", {})
                        city = props.get("city") or props.get("name") or props.get("county") or clean_q
                        country = props.get("country", "")
                        return lat, lon, city, country, None
        except Exception:
            pass
        return None

    def _query_nominatim(self, query: str) -> Optional[tuple[float, float, str, str, Optional[str]]]:
        """Queries OpenStreetMap Nominatim as tertiary fallback."""
        try:
            location = self._geolocator.geocode(query, addressdetails=True)
            if location:
                raw_address = location.raw.get("address", {})
                city = (
                    raw_address.get("city")
                    or raw_address.get("town")
                    or raw_address.get("village")
                    or raw_address.get("county")
                    or location.address.split(",")[0]
                )
                country = raw_address.get("country", "")
                return location.latitude, location.longitude, city, country, None
        except Exception:
            pass
        return None

    def geocode(
        self,
        query: str,
    ) -> tuple[float, float, Optional[str], Optional[str]]:
        """Geocodes an address or city query to (latitude, longitude, city, country).

        Utilizes a resilient 5-tier resolution pipeline:
        1. Direct coordinate numeric parsing
        2. In-memory LRU cache
        3. Offline Curated Cities Database (instant 0ms response)
        4. Open-Meteo Geocoding API (cloud-friendly, free, no rate blocks)
        5. Photon by Komoot & Nominatim fallbacks

        Args:
            query: Address, city, or location string.

        Returns:
            Tuple of (latitude, longitude, city_name, country_name).

        Raises:
            ValueError: If the location query cannot be resolved.
        """
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Location query cannot be empty.")

        # Tier 0: Direct coordinates (e.g. "26.9124, 75.7873")
        coords = self._try_parse_coordinates(clean_query)
        if coords:
            return coords

        norm_key = clean_query.lower()

        # Tier 1: In-memory cache
        if norm_key in self._cache:
            return self._cache[norm_key]

        # Tier 2: Offline Curated Cities Database
        lookup_candidates = [norm_key]
        if "," in norm_key:
            lookup_candidates.append(norm_key.split(",")[0].strip())

        for candidate in lookup_candidates:
            if candidate in OFFLINE_CITIES:
                lat, lon, city, country, tz = OFFLINE_CITIES[candidate]
                self._tz_cache[(round(lat, 4), round(lon, 4))] = tz
                result = (lat, lon, city, country)
                self._cache[norm_key] = result
                return result

        # Tier 3: Open-Meteo Geocoding API (Primary Cloud Resolver)
        om_res = self._query_open_meteo(clean_query)
        if om_res:
            lat, lon, city, country, tz = om_res
            if tz:
                self._tz_cache[(round(lat, 4), round(lon, 4))] = tz
            result = (lat, lon, city, country)
            self._cache[norm_key] = result
            return result

        # Tier 4: Photon Geocoding API (Secondary Cloud Resolver)
        ph_res = self._query_photon(clean_query)
        if ph_res:
            lat, lon, city, country, _ = ph_res
            result = (lat, lon, city, country)
            self._cache[norm_key] = result
            return result

        # Tier 5: Nominatim (Tertiary Fallback)
        nom_res = self._query_nominatim(clean_query)
        if nom_res:
            lat, lon, city, country, _ = nom_res
            result = (lat, lon, city, country)
            self._cache[norm_key] = result
            return result

        raise ValueError(f"Could not resolve coordinates for location: '{query}'. Please verify the spelling or enter coordinates manually.")

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
