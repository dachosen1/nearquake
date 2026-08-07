"""Statistical analysis of aircraft type-vintage age by destination region.

Three layers, from simplest to most controlled:

1. Descriptive: mean type-vintage age by region, overall and per carrier.
2. Two-sample tests: Welch's t-test and the non-parametric Mann-Whitney U,
   comparing African routes against the pooled comparison regions (Europe /
   Asia / North America), overall and per carrier.
3. OLS regression: type_vintage_age ~ is_africa + controls (route distance,
   widebody indicator, destination connectivity) + carrier fixed effects, with
   heteroskedasticity-robust (HC3) standard errors. The coefficient on
   ``is_africa`` is the confounder-adjusted estimate of the age gap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from . import config


def descriptive_by_region(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("region")["type_vintage_age"]
    out = pd.DataFrame(
        {
            "n": g.size(),
            "mean_age": g.mean(),
            "median_age": g.median(),
            "std_age": g.std(),
        }
    )
    # Companion: mean route distance and widebody share, to expose confounding.
    out["mean_distance_km"] = df.groupby("region")["distance_km"].mean()
    out["widebody_share"] = df.groupby("region")["is_widebody"].mean()
    return out.sort_values("mean_age", ascending=False)


def descriptive_by_carrier_region(df: pd.DataFrame) -> pd.DataFrame:
    tab = df.pivot_table(
        index="carrier_name",
        columns="region",
        values="type_vintage_age",
        aggfunc="mean",
    )
    ordered = [config.REGION_AFRICA] + config.COMPARISON_REGIONS
    cols = [c for c in ordered if c in tab.columns]
    return tab[cols]


def _two_sample(africa: np.ndarray, other: np.ndarray) -> dict:
    if len(africa) < 3 or len(other) < 3:
        return {"n_africa": len(africa), "n_other": len(other), "insufficient": True}
    t_stat, t_p = stats.ttest_ind(africa, other, equal_var=False)  # Welch
    u_stat, u_p = stats.mannwhitneyu(africa, other, alternative="two-sided")
    # Cohen's d (pooled sd).
    pooled_sd = np.sqrt(
        ((len(africa) - 1) * africa.var(ddof=1) + (len(other) - 1) * other.var(ddof=1))
        / (len(africa) + len(other) - 2)
    )
    cohens_d = (africa.mean() - other.mean()) / pooled_sd if pooled_sd else np.nan
    return {
        "n_africa": len(africa),
        "n_other": len(other),
        "mean_africa": float(africa.mean()),
        "mean_other": float(other.mean()),
        "mean_diff": float(africa.mean() - other.mean()),
        "welch_t": float(t_stat),
        "welch_p": float(t_p),
        "mannwhitney_u": float(u_stat),
        "mannwhitney_p": float(u_p),
        "cohens_d": float(cohens_d),
        "insufficient": False,
    }


def ttests(df: pd.DataFrame) -> pd.DataFrame:
    """Africa vs. pooled comparison regions, overall and per carrier."""
    comp = df[df["region"].isin(config.COMPARISON_REGIONS)]
    afr = df[df["region"] == config.REGION_AFRICA]

    rows = []
    overall = _two_sample(
        afr["type_vintage_age"].to_numpy(), comp["type_vintage_age"].to_numpy()
    )
    overall["carrier"] = "ALL CARRIERS"
    rows.append(overall)

    for code, name in config.CARRIERS.items():
        a = afr[afr["airline"] == code]["type_vintage_age"].to_numpy()
        o = comp[comp["airline"] == code]["type_vintage_age"].to_numpy()
        res = _two_sample(a, o)
        res["carrier"] = name
        rows.append(res)

    return pd.DataFrame(rows).set_index("carrier")


def regression(df: pd.DataFrame):
    """OLS with controls + carrier fixed effects, HC3 robust SEs.

    Restricted to Africa + comparison regions so ``is_africa`` contrasts against
    a well-defined baseline (Europe/Asia/North America).
    """
    d = df[df["region"].isin([config.REGION_AFRICA] + config.COMPARISON_REGIONS)].copy()
    d["distance_1000km"] = d["distance_km"] / 1000.0
    d["connectivity_100"] = d["dest_connectivity"] / 100.0

    formula = (
        "type_vintage_age ~ is_africa + distance_1000km + is_widebody "
        "+ connectivity_100 + C(airline)"
    )
    model = smf.ols(formula, data=d).fit(cov_type="HC3")
    return model


def format_report(desc_region, desc_cr, tt, model) -> str:
    lines = []
    lines.append("MEAN TYPE-VINTAGE AGE BY DESTINATION REGION (years, all carriers)")
    lines.append(desc_region.round(2).to_string())
    lines.append("")
    lines.append("MEAN TYPE-VINTAGE AGE BY CARRIER x REGION (years)")
    lines.append(desc_cr.round(2).to_string())
    lines.append("")
    lines.append("AFRICA vs (EUROPE/ASIA/NORTH AMERICA) -- two-sample tests")
    show = tt[
        [
            "n_africa",
            "n_other",
            "mean_africa",
            "mean_other",
            "mean_diff",
            "welch_p",
            "mannwhitney_p",
            "cohens_d",
        ]
    ]
    lines.append(show.round(4).to_string())
    lines.append("")
    lines.append(
        "OLS REGRESSION (HC3 robust SE): type_vintage_age ~ is_africa + controls"
    )
    lines.append(str(model.summary()))
    return "\n".join(lines)
