"""End-to-end runner for the aircraft-age-by-region analysis.

Usage
-----
    python run_analysis.py                 # real OpenFlights analysis + figures
    python run_analysis.py --demo-tails    # also run the tail-level demo design

Outputs (written to ./outputs/):
    analysis_dataset.csv          the built route-level dataset
    stats_report.txt              descriptives, t-tests, regression summary
    diagnostics.json              dataset build diagnostics / coverage
    fig1..fig4 *.png              visualisations
    tail_level_demo_report.txt    (only with --demo-tails) illustrative tail model
"""

from __future__ import annotations

import argparse
import json
import os

from aircraft_age import analyze, build_dataset, config, visualize


def run_real() -> None:
    print("=" * 70)
    print("REAL-DATA ANALYSIS (OpenFlights routes + aircraft type vintage)")
    print("=" * 70)
    df, diag = build_dataset.build()

    ds_path = os.path.join(config.OUTPUT_DIR, "analysis_dataset.csv")
    df.to_csv(ds_path, index=False)
    print(f"[out] dataset -> {ds_path}  ({len(df)} observations)")

    with open(os.path.join(config.OUTPUT_DIR, "diagnostics.json"), "w") as fh:
        json.dump(diag, fh, indent=2, default=str)

    desc_region = analyze.descriptive_by_region(df)
    desc_cr = analyze.descriptive_by_carrier_region(df)
    tt = analyze.ttests(df)
    model = analyze.regression(df)

    report = analyze.format_report(desc_region, desc_cr, tt, model)
    report_path = os.path.join(config.OUTPUT_DIR, "stats_report.txt")
    with open(report_path, "w") as fh:
        fh.write(report)
    print(f"[out] stats report -> {report_path}")
    print("\n" + report)

    figs = visualize.generate_all(df)
    for p in figs:
        print(f"[out] figure -> {p}")


def run_demo_tails() -> None:
    from aircraft_age import synthetic_fleet

    print("\n" + "=" * 70)
    print("TAIL-LEVEL DEMO (ILLUSTRATIVE / SIMULATED DATA -- NOT OBSERVATIONS)")
    print("=" * 70)
    df = synthetic_fleet.generate_demo_tail_data()
    desc_region = analyze.descriptive_by_region(df)
    tt = analyze.ttests(df)
    model = analyze.regression(df)

    header = (
        "TAIL-LEVEL DEMO -- SIMULATED DATA, ILLUSTRATIVE ONLY.\n"
        "Numbers below are produced by a calibrated generator, not observed\n"
        "flights. They demonstrate that the pipeline detects a true airframe-age\n"
        "gap once real tail<->route data is supplied. See synthetic_fleet.py.\n"
        + "=" * 70
        + "\n"
    )
    report = header + analyze.format_report(
        desc_region, analyze.descriptive_by_carrier_region(df), tt, model
    )
    path = os.path.join(config.OUTPUT_DIR, "tail_level_demo_report.txt")
    with open(path, "w") as fh:
        fh.write(report)
    print(f"[out] tail-level demo report -> {path}")
    print("\n" + report)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--demo-tails",
        action="store_true",
        help="also run the illustrative tail-number-level design",
    )
    args = ap.parse_args()
    run_real()
    if args.demo_tails:
        run_demo_tails()


if __name__ == "__main__":
    main()
