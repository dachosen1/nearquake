"""Download, cache, and normalise the open route/airport reference data.

Primary source: **OpenFlights** (https://openflights.org/data.html), a public,
openly-licensed dataset mirrored on GitHub. It provides:

* ``routes.dat``   -- airline, source/destination airport, and the IATA
                      equipment (aircraft type) codes assigned to each route.
* ``airports.dat`` -- airport -> country + latitude/longitude, used for region
                      assignment and great-circle distance.

Live per-tail registries (OpenSky, planespotters, ch-aviation) and historical
flight-tracking feeds (FlightAware, Flightradar24, OAG) are the sources the
ideal design would use, but they are paywalled and/or unreachable from this
environment. See ``synthetic_fleet.py`` for the tail-level design that plugs in
once such data is available.
"""

from __future__ import annotations

import os
import urllib.request
from math import asin, cos, radians, sin, sqrt

import pandas as pd
import pycountry_convert as pcc

from . import config

# Columns per the OpenFlights schema (files have no header row).
_ROUTES_COLS = [
    "airline", "airline_id", "src", "src_id", "dst", "dst_id",
    "codeshare", "stops", "equipment",
]
_AIRPORTS_COLS = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "lat", "lon", "alt", "timezone", "dst", "tz", "type", "source",
]

# Continent-code -> human-readable region used throughout the analysis.
_CONTINENT_TO_REGION = {
    "AF": config.REGION_AFRICA,
    "EU": config.REGION_EUROPE,
    "AS": config.REGION_ASIA,
    "NA": config.REGION_NORTH_AMERICA,
    "SA": config.REGION_SOUTH_AMERICA,
    "OC": config.REGION_OCEANIA,
}

# OpenFlights country names that pycountry_convert does not resolve directly.
_COUNTRY_FIXUPS = {
    "Congo (Kinshasa)": "Africa",
    "Congo (Brazzaville)": "Africa",
    "Ivory Coast": "Africa",
    "Cape Verde": "Africa",
    "Tanzania": "Africa",
    "Reunion": "Africa",
    "Western Sahara": "Africa",
    "South Sudan": "Africa",
    "Burma": "Asia",
    "Macau": "Asia",
    "West Bank": "Asia",
    "Timor-Leste": "Asia",
    "Kosovo": "Europe",
    "Netherlands Antilles": "North America",
    "Virgin Islands": "North America",
    "Saint Barthelemy": "North America",
    "Curacao": "North America",
    "Cocos (Keeling) Islands": "Asia",
}


def _cache_path(name: str) -> str:
    return os.path.join(config.DATA_CACHE_DIR, f"{name}.dat")


def download_openflights(force: bool = False) -> None:
    """Fetch the OpenFlights files into the local cache if not already present."""
    for name, url in config.OPENFLIGHTS_FILES.items():
        path = _cache_path(name)
        if os.path.exists(path) and not force:
            continue
        print(f"[data] downloading {name} <- {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "aircraft-age-analysis/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(path, "wb") as fh:
            fh.write(data)


def load_routes() -> pd.DataFrame:
    df = pd.read_csv(
        _cache_path("routes"), names=_ROUTES_COLS, na_values=["\\N"], keep_default_na=True,
    )
    return df


def load_airports() -> pd.DataFrame:
    df = pd.read_csv(
        _cache_path("airports"), names=_AIRPORTS_COLS, na_values=["\\N"], keep_default_na=True,
    )
    return df


def country_to_region(country: str) -> str | None:
    """Map an OpenFlights country name to one of the analysis regions."""
    if not isinstance(country, str) or not country:
        return None
    if country in _COUNTRY_FIXUPS:
        return _COUNTRY_FIXUPS[country]
    try:
        alpha2 = pcc.country_name_to_country_alpha2(country)
        continent = pcc.country_alpha2_to_continent_code(alpha2)
    except (KeyError, ValueError):
        return None
    return _CONTINENT_TO_REGION.get(continent)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometres."""
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))
