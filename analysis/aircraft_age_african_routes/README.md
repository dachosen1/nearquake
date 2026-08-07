# Do major carriers fly older aircraft on African routes?

A self-contained, reproducible Python study of whether major international
carriers deploy **older aircraft on routes to Africa** than on comparable routes
to Europe, Asia, and North America.

> **Note on scope.** This project lives inside the `nearquake` repo but is an
> independent analytical deliverable — it does not touch the earthquake bot's
> code or dependencies. It has its own `requirements.txt` and venv.

---

## TL;DR of the findings

Using real route + aircraft-type data for six carriers (Air France, KLM, British
Airways, Emirates, Turkish, Ethiopian) and an **aircraft type-vintage age proxy**
(years since the assigned aircraft *type* entered service):

- **No broad, systematic "oldest planes to Africa" effect** at the aircraft-type
  level. Overall Africa vs. (Europe/Asia/N. America): mean gap **+0.43 years**,
  not significant (Welch *p* = 0.20; regression-adjusted `is_africa` coefficient
  **−0.15 yr**, *p* = 0.65).
- **The pattern is carrier-specific.** British Airways *does* fly markedly
  older-vintage types to Africa (**+4.4 yr**, *p* < 0.001); KLM and Air France do
  the *opposite* (younger to Africa); Emirates and Turkish show no difference.
- **Route distance is a real confounder**: longer routes get newer-vintage types
  (−0.25 yr per 1,000 km, *p* < 0.001), and it is controlled for in the regression.

The single biggest caveat: the reachable data supports only a *type-vintage*
proxy, **not true per-airframe age**. The most plausible channel for the
hypothesis — a carrier sending its *oldest individual airframes of a given type*
to Africa — is invisible to type-level data. The tail-number-level design that
*would* capture it is implemented (`aircraft_age/synthetic_fleet.py`) and runs on
demo data, ready for real historical inputs. See [`FINDINGS.md`](FINDINGS.md).

---

## How to run

```bash
cd analysis/aircraft_age_african_routes
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Real-data analysis + figures:
.venv/bin/python run_analysis.py

# Also run the illustrative tail-number-level design on demo data:
.venv/bin/python run_analysis.py --demo-tails
```

Outputs are written to [`outputs/`](outputs/) (committed, so results are visible
without running):

| File | Contents |
|------|----------|
| `analysis_dataset.csv`        | The built route-level dataset (one row per carrier × route × aircraft type) |
| `stats_report.txt`            | Descriptives, t-tests, and the OLS regression summary |
| `diagnostics.json`            | Build diagnostics, coverage, unmapped equipment codes |
| `fig1_age_distribution_by_region.png` | Type-vintage age distribution by region |
| `fig2_mean_age_by_carrier_region.png` | Mean age by carrier × region |
| `fig3_age_vs_distance.png`    | Age vs. route distance (confounder) |
| `fig4_body_type_mix_by_region.png` | Body-type mix by region (confounder) |
| `tail_level_demo_report.txt`  | Illustrative tail-level model (simulated data) |

---

## Method

### Definition of "old"
Live per-tail registries (planespotters, OpenSky, ch-aviation) and historical
flight-tracking (FlightAware / Flightradar24 / OAG) — the sources needed for true
airframe age — are paywalled and/or blocked from this environment. We therefore
define:

```
type_vintage_age = ANALYSIS_YEAR (2024) − aircraft type entry-into-service year
```

i.e. the generational age of the *equipment a carrier chooses to deploy* on a
route. It is a lower bound on, and a strong correlate of, physical airframe age.
EIS years live in `aircraft_age/aircraft_reference.py` (manufacturer type-cert
histories).

### Airlines
Six major carriers with significant African networks (`aircraft_age/config.py`):
Air France (AF), KLM (KL), British Airways (BA), Emirates (EK), Turkish (TK),
Ethiopian (ET).

### Comparison regions
Destination continent of each route. **Africa** (treatment) vs. **Europe /
Asia / North America** (comparison), per the task definition. Assigned by mapping
the destination airport's country to a continent (`pycountry_convert`).

### Dataset construction (`aircraft_age/build_dataset.py`)
One observation per `(carrier, source, destination, aircraft type)`. Each route's
equipment list is exploded so every equipment-assignment decision is a row. Each
observation carries: destination region, type-vintage age, great-circle distance
(control), widebody indicator (control), and destination-airport connectivity
(demand proxy control).

### Statistics (`aircraft_age/analyze.py`)
1. **Descriptives** — mean/median age by region, overall and per carrier.
2. **Two-sample tests** — Welch's *t*-test + Mann-Whitney U, with Cohen's *d*,
   Africa vs. pooled comparison regions, overall and per carrier.
3. **OLS regression** with HC3 robust SEs and carrier fixed effects:
   ```
   type_vintage_age ~ is_africa + distance + is_widebody + connectivity + C(airline)
   ```
   The `is_africa` coefficient is the confounder-adjusted age gap.

### The ideal tail-level design (`aircraft_age/synthetic_fleet.py`)
Implements the full airframe-level pipeline (tail → build year → route → region).
It runs on a **clearly-labelled simulated** dataset here; swapping in a real
`tail_flights` table (schema documented in the module) makes it a real study with
no other code changes.

## Data sources
- **OpenFlights** (`routes.dat`, `airports.dat`) — open, GitHub-mirrored; routes,
  equipment codes, airport geography. Auto-downloaded to `data_cache/`.
- **Aircraft type EIS years** — curated in `aircraft_reference.py` from standard
  manufacturer/type-certificate references.
- *(Not reachable here, needed for the ideal design)* per-tail registries and
  historical flight tracking.

See [`FINDINGS.md`](FINDINGS.md) for the full write-up and limitations.
