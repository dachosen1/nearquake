"""Figures for the aircraft-age-by-region analysis.

Uses matplotlib only (no seaborn dependency). Every figure is written to the
outputs/ directory as PNG.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config

_REGION_ORDER = [
    config.REGION_AFRICA,
    config.REGION_EUROPE,
    config.REGION_ASIA,
    config.REGION_NORTH_AMERICA,
    config.REGION_SOUTH_AMERICA,
    config.REGION_OCEANIA,
]
# Highlight Africa; muted grey for the rest.
_AFRICA_COLOR = "#c0392b"
_OTHER_COLOR = "#5b6c7d"


def _regions_present(df: pd.DataFrame) -> list[str]:
    return [r for r in _REGION_ORDER if r in set(df["region"])]


def age_distribution_by_region(df: pd.DataFrame, path: str) -> None:
    regions = _regions_present(df)
    data = [df[df["region"] == r]["type_vintage_age"].to_numpy() for r in regions]
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(data, tick_labels=regions, showmeans=True, patch_artist=True)
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(
            _AFRICA_COLOR if regions[i] == config.REGION_AFRICA else _OTHER_COLOR
        )
        box.set_alpha(0.65)
    for mean in bp["means"]:
        mean.set_marker("D")
        mean.set_markerfacecolor("white")
        mean.set_markeredgecolor("black")
    ax.set_ylabel(f"Aircraft type-vintage age (years, ref {config.ANALYSIS_YEAR})")
    ax.set_title(
        "Aircraft type-vintage age by destination region\n"
        "(6 major carriers with African networks; Africa highlighted)"
    )
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def mean_age_by_carrier_region(df: pd.DataFrame, path: str) -> None:
    ordered_regions = [config.REGION_AFRICA] + config.COMPARISON_REGIONS
    carriers = list(config.CARRIERS.values())
    tab = df.pivot_table(
        index="carrier_name",
        columns="region",
        values="type_vintage_age",
        aggfunc="mean",
    )
    tab = tab.reindex(index=carriers, columns=ordered_regions)

    x = np.arange(len(carriers))
    width = 0.2
    fig, ax = plt.subplots(figsize=(12, 6.5))
    palette = {
        config.REGION_AFRICA: _AFRICA_COLOR,
        config.REGION_EUROPE: "#2e86c1",
        config.REGION_ASIA: "#28b463",
        config.REGION_NORTH_AMERICA: "#8e44ad",
    }
    for i, region in enumerate(ordered_regions):
        vals = tab[region].to_numpy()
        ax.bar(
            x + (i - 1.5) * width,
            vals,
            width,
            label=region,
            color=palette.get(region, _OTHER_COLOR),
            alpha=0.9,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(carriers, rotation=20, ha="right")
    ax.set_ylabel(f"Mean type-vintage age (years, ref {config.ANALYSIS_YEAR})")
    ax.set_title("Mean aircraft type-vintage age by carrier and destination region")
    ax.legend(title="Destination region")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def age_vs_distance(df: pd.DataFrame, path: str) -> None:
    """Scatter exposing the distance confounder: Africa vs. comparison regions."""
    comp = df[df["region"].isin(config.COMPARISON_REGIONS)]
    afr = df[df["region"] == config.REGION_AFRICA]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        comp["distance_km"],
        comp["type_vintage_age"],
        s=10,
        alpha=0.25,
        color=_OTHER_COLOR,
        label="Europe / Asia / N. America",
    )
    ax.scatter(
        afr["distance_km"],
        afr["type_vintage_age"],
        s=14,
        alpha=0.5,
        color=_AFRICA_COLOR,
        label="Africa",
    )
    ax.set_xlabel("Great-circle route distance (km)")
    ax.set_ylabel(f"Aircraft type-vintage age (years, ref {config.ANALYSIS_YEAR})")
    ax.set_title("Type-vintage age vs. route distance\n(distance is a key confounder)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def body_type_mix_by_region(df: pd.DataFrame, path: str) -> None:
    regions = [
        r
        for r in ([config.REGION_AFRICA] + config.COMPARISON_REGIONS)
        if r in set(df["region"])
    ]
    mix = (
        df[df["region"].isin(regions)]
        .groupby(["region", "body"])
        .size()
        .unstack(fill_value=0)
    )
    mix = mix.reindex(index=regions)
    mix_share = mix.div(mix.sum(axis=1), axis=0)

    body_order = [
        c
        for c in ["widebody", "narrowbody", "regional_jet", "turboprop"]
        if c in mix_share.columns
    ]
    mix_share = mix_share[body_order]
    colors = {
        "widebody": "#1f618d",
        "narrowbody": "#5dade2",
        "regional_jet": "#f5b041",
        "turboprop": "#af7ac5",
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(regions))
    for body in body_order:
        vals = mix_share[body].to_numpy()
        ax.bar(
            regions,
            vals,
            bottom=bottom,
            label=body.replace("_", " "),
            color=colors.get(body),
            alpha=0.9,
        )
        bottom += vals
    ax.set_ylabel("Share of equipment assignments")
    ax.set_title(
        "Aircraft body-type mix by destination region\n"
        "(body type constrains and confounds age comparisons)"
    )
    ax.legend(title="Body type", loc="lower right")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def generate_all(df: pd.DataFrame, out_dir: str | None = None) -> list[str]:
    out_dir = out_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "fig1_age_distribution_by_region.png": age_distribution_by_region,
        "fig2_mean_age_by_carrier_region.png": mean_age_by_carrier_region,
        "fig3_age_vs_distance.png": age_vs_distance,
        "fig4_body_type_mix_by_region.png": body_type_mix_by_region,
    }
    written = []
    for fname, fn in paths.items():
        p = os.path.join(out_dir, fname)
        fn(df, p)
        written.append(p)
    return written
