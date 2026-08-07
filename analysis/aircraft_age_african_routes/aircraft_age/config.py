"""Analysis configuration: carriers, regions, and paths.

Edit ``CARRIERS`` or ``ANALYSIS_YEAR`` to re-scope the study. Everything
downstream (dataset build, statistics, plots) reads from here.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

# Reference year against which type-vintage age is measured
# (age = ANALYSIS_YEAR - aircraft type entry-into-service year).
ANALYSIS_YEAR = 2024

# Major international carriers with significant African route networks.
# Keyed by 2-letter IATA airline code (as used in OpenFlights routes.dat).
CARRIERS: dict[str, str] = {
    "AF": "Air France",
    "KL": "KLM",
    "BA": "British Airways",
    "EK": "Emirates",
    "TK": "Turkish Airlines",
    "ET": "Ethiopian Airlines",
}

# Continent buckets produced by the country->region mapper.
REGION_AFRICA = "Africa"
REGION_EUROPE = "Europe"
REGION_ASIA = "Asia"
REGION_NORTH_AMERICA = "North America"
REGION_SOUTH_AMERICA = "South America"
REGION_OCEANIA = "Oceania"

# The task defines the comparison as African routes vs. European, Asian and
# North American routes from the same carriers. These are the "comparison"
# regions used for the primary two-sample tests.
COMPARISON_REGIONS = [REGION_EUROPE, REGION_ASIA, REGION_NORTH_AMERICA]

# The treatment group for the primary hypothesis.
TREATMENT_REGION = REGION_AFRICA

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(_PKG_DIR)
DATA_CACHE_DIR = os.path.join(PROJECT_DIR, "data_cache")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")

os.makedirs(DATA_CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# OpenFlights open data (route + airport reference), mirrored on GitHub.
OPENFLIGHTS_BASE = "https://raw.githubusercontent.com/jpatokal/openflights/master/data"
OPENFLIGHTS_FILES = {
    "routes": f"{OPENFLIGHTS_BASE}/routes.dat",
    "airports": f"{OPENFLIGHTS_BASE}/airports.dat",
    "airlines": f"{OPENFLIGHTS_BASE}/airlines.dat",
}
