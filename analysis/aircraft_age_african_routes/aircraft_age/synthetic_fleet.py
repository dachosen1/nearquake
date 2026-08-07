"""Tail-number-level design -- the *ideal* methodology, runnable on demo data.

WHAT THIS IS
------------
The task's ideal design links a **specific airframe (tail number) of known
manufacture date** to the **specific route/region it operated** over a time
window, then compares true airframe age across regions. That requires historical
flight-tracking data (Flightradar24 / FlightAware / OpenSky state vectors) joined
to a tail-age registry (planespotters / ch-aviation / OpenSky metadata). Those
feeds are paywalled and/or blocked from this environment, so no such real dataset
could be built here.

This module implements the full pipeline anyway, so that:

  1. the statistical code in ``analyze.py`` runs end-to-end at tail granularity, and
  2. dropping in a real ``tail_flights`` table (columns documented in
     ``TAIL_FLIGHTS_SCHEMA``) makes the analysis real with no other changes.

IMPORTANT: ``generate_demo_tail_data`` produces **simulated** rows. They are
deterministic (fixed seed) and calibrated to plausible fleet behaviour, but they
are NOT observations. Numbers derived from them are illustrative only and are
reported separately from the real OpenFlights results, clearly labelled.

REAL-DATA CONTRACT
------------------
Replace ``generate_demo_tail_data`` with a loader returning a DataFrame with the
columns in ``TAIL_FLIGHTS_SCHEMA``; everything downstream is source-agnostic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

TAIL_FLIGHTS_SCHEMA = {
    "airline": "IATA carrier code",
    "tail_number": "aircraft registration, e.g. 'ET-AVN'",
    "build_year": "airframe manufacture year (from tail registry)",
    "region": "destination region the airframe operated to on this flight",
    "distance_km": "great-circle distance of the flown sector",
    "is_widebody": "1 if widebody, else 0",
    "dest_connectivity": "demand proxy for the destination airport",
    "flight_date": "date the sector was flown (within the analysis window)",
}

# Assumed real-world fleet ages by carrier (mean airframe age, years) used only
# to calibrate the demo simulation. Rough, illustrative figures.
_DEMO_FLEET_MEAN_AGE = {
    "AF": 12.5, "KL": 11.5, "BA": 13.0, "EK": 7.0, "TK": 8.5, "ET": 6.5,
}
# Assumed extra age (years) an airframe carries when assigned to an African
# sector, holding the carrier fixed -- the effect the design is built to detect.
_DEMO_AFRICA_AGE_PREMIUM = 2.5


def generate_demo_tail_data(n_per_carrier: int = 400, seed: int = 12345) -> pd.DataFrame:
    """Return SIMULATED tail-level flight observations (illustrative only)."""
    rng = np.random.default_rng(seed)
    regions = [config.REGION_AFRICA] + config.COMPARISON_REGIONS
    # Region base sector distances (km) -- Africa mixes medium/long haul.
    region_dist = {
        config.REGION_AFRICA: 5200, config.REGION_EUROPE: 1200,
        config.REGION_ASIA: 6500, config.REGION_NORTH_AMERICA: 6800,
    }
    rows = []
    for code in config.CARRIERS:
        base_age = _DEMO_FLEET_MEAN_AGE.get(code, 10.0)
        for _ in range(n_per_carrier):
            region = rng.choice(regions, p=[0.25, 0.4, 0.2, 0.15])
            dist = max(300, rng.normal(region_dist[region], region_dist[region] * 0.25))
            is_wb = 1 if dist > 4000 else int(rng.random() < 0.1)
            africa_premium = _DEMO_AFRICA_AGE_PREMIUM if region == config.REGION_AFRICA else 0.0
            age = max(0.5, rng.normal(base_age + africa_premium, 4.0))
            build_year = int(round(config.ANALYSIS_YEAR - age))
            rows.append({
                "airline": code,
                "tail_number": f"{code}-{rng.integers(1000, 9999)}",
                "build_year": build_year,
                "region": region,
                "distance_km": round(dist, 1),
                "is_widebody": is_wb,
                "dest_connectivity": int(max(20, rng.normal(400, 200))),
                "flight_date": "2024-01-01",
            })
    df = pd.DataFrame(rows)
    df["carrier_name"] = df["airline"].map(config.CARRIERS)
    # True airframe age -- the real target variable, named to match analyze.py.
    df["type_vintage_age"] = config.ANALYSIS_YEAR - df["build_year"]
    df["is_africa"] = (df["region"] == config.REGION_AFRICA).astype(int)
    return df
