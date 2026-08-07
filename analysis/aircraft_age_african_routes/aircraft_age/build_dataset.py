"""Build the route-level analysis dataset from the open reference data.

Output granularity: one row per (carrier, source, destination, aircraft type).
A route that lists several equipment codes is *exploded* into one observation per
code, because each code is a distinct equipment-assignment decision by the
carrier. Each observation carries the fields needed for the statistical model:

  * region            -- destination continent (treatment: Africa)
  * type_vintage_age  -- ANALYSIS_YEAR - aircraft type EIS year (proxy for age)
  * distance_km       -- great-circle source->destination distance (control)
  * body              -- narrowbody / widebody / regional_jet / turboprop (control)
  * dest_connectivity -- # of routes (all airlines) into the destination airport,
                         a proxy for airport size / demand (control)
"""

from __future__ import annotations

import pandas as pd

from . import config, data_sources
from .aircraft_reference import lookup


def _explode_equipment(routes: pd.DataFrame) -> pd.DataFrame:
    """One row per (route, equipment code)."""
    routes = routes.copy()
    routes["equipment"] = routes["equipment"].fillna("").astype(str).str.strip()
    routes = routes[routes["equipment"] != ""]
    routes["equipment"] = routes["equipment"].str.split()
    return routes.explode("equipment", ignore_index=True)


def build() -> tuple[pd.DataFrame, dict]:
    """Return (analysis_dataframe, diagnostics_dict)."""
    data_sources.download_openflights()
    routes = data_sources.load_routes()
    airports = data_sources.load_airports()

    diag: dict = {}

    # Destination airport connectivity across ALL airlines = demand proxy.
    dest_connectivity = (
        routes.groupby("dst").size().rename("dest_connectivity").reset_index()
    )

    # Airport lookup: region + coordinates (keyed by IATA code).
    ap = airports.dropna(subset=["iata", "lat", "lon"]).copy()
    ap = ap[ap["iata"].str.len() == 3]
    ap["region"] = ap["country"].map(data_sources.country_to_region)
    ap_by_iata = ap.set_index("iata")

    # Restrict to the analysed carriers.
    routes = routes[routes["airline"].isin(config.CARRIERS)].copy()
    diag["carrier_route_records"] = len(routes)

    obs = _explode_equipment(routes)
    diag["equipment_assignments"] = len(obs)

    # Attach aircraft-type reference (EIS year, body type, seats).
    ref = obs["equipment"].map(lookup)
    known = ref.notna()
    diag["unknown_equipment_codes"] = sorted(
        obs.loc[~known, "equipment"].value_counts().to_dict().items(),
        key=lambda kv: -kv[1],
    )
    obs = obs[known].copy()
    ref = ref[known]
    obs["aircraft_name"] = ref.map(lambda a: a.name)
    obs["eis_year"] = ref.map(lambda a: a.eis_year)
    obs["body"] = ref.map(lambda a: a.body)
    obs["seats"] = ref.map(lambda a: a.seats)
    obs["type_vintage_age"] = config.ANALYSIS_YEAR - obs["eis_year"]

    # Attach source & destination geography.
    for side in ("src", "dst"):
        obs = obs.join(
            ap_by_iata[["lat", "lon", "region", "country"]].rename(
                columns={
                    "lat": f"{side}_lat",
                    "lon": f"{side}_lon",
                    "region": f"{side}_region",
                    "country": f"{side}_country",
                }
            ),
            on=side,
        )

    # Region of the ROUTE = destination region (task defines routes by where the
    # carrier flies *to*).
    obs["region"] = obs["dst_region"]

    # Great-circle distance.
    have_coords = obs[["src_lat", "src_lon", "dst_lat", "dst_lon"]].notna().all(axis=1)
    obs = obs[have_coords].copy()
    obs["distance_km"] = obs.apply(
        lambda r: data_sources.haversine_km(
            r["src_lat"], r["src_lon"], r["dst_lat"], r["dst_lon"]
        ),
        axis=1,
    )

    # Demand proxy.
    obs = obs.merge(dest_connectivity, on="dst", how="left")
    obs["dest_connectivity"] = obs["dest_connectivity"].fillna(0).astype(int)

    obs = obs.dropna(subset=["region"]).copy()
    obs["carrier_name"] = obs["airline"].map(config.CARRIERS)
    obs["is_widebody"] = (obs["body"] == "widebody").astype(int)
    obs["is_africa"] = (obs["region"] == config.REGION_AFRICA).astype(int)

    cols = [
        "airline",
        "carrier_name",
        "src",
        "dst",
        "dst_country",
        "region",
        "equipment",
        "aircraft_name",
        "eis_year",
        "type_vintage_age",
        "body",
        "is_widebody",
        "seats",
        "distance_km",
        "dest_connectivity",
        "is_africa",
    ]
    obs = obs[cols].reset_index(drop=True)
    diag["final_observations"] = len(obs)
    diag["observations_by_region"] = obs["region"].value_counts().to_dict()
    return obs, diag


if __name__ == "__main__":
    df, diagnostics = build()
    print(df.head())
    for k, v in diagnostics.items():
        print(f"{k}: {v}")
