"""Reference table of aircraft types used by the analysed carriers.

The public route data (OpenFlights) records the *type* of aircraft assigned to
each route via IATA equipment codes, but it does **not** record the tail number
or the manufacture date of the specific airframe. Live per-tail registries
(OpenSky, planespotters, ch-aviation) are not reachable from this environment,
so we cannot compute the true airframe age of the exact aircraft on each flight.

Instead we use a defensible, fully-transparent proxy: the **entry-into-service
(EIS) year** of the aircraft *type/variant*. The "type vintage age" of a route
in a given analysis year is::

    type_vintage_age = analysis_year - eis_year

This measures the generational age of the equipment a carrier chooses to deploy
on a route. It is a *lower bound* on, and a strong correlate of, the physical
airframe age: a type that entered service in 1998 cannot have airframes newer
than that generation, and carriers tend to retire and re-deploy older-generation
types onto lower-yield markets. The proxy is explicitly type-level, not
airframe-level -- see FINDINGS.md and README.md for the resulting limitations.

EIS years below are the widely-published in-service dates of the family or the
representative variant behind each IATA code. Sources: manufacturer type
certificates and standard aviation references (Airbus/Boeing/Embraer/Bombardier
/ATR programme histories). Where an IATA code is generic (e.g. "777"), the base
variant's EIS is used and noted in ``notes``.
"""

from __future__ import annotations

from dataclasses import dataclass

# Body-type buckets used as a regression control and in plots.
NARROWBODY = "narrowbody"
WIDEBODY = "widebody"
REGIONAL_JET = "regional_jet"
TURBOPROP = "turboprop"


@dataclass(frozen=True)
class AircraftType:
    code: str  # IATA equipment code as it appears in OpenFlights routes.dat
    name: str
    eis_year: int  # entry-into-service year of the family / representative variant
    body: str  # one of the buckets above
    seats: int  # typical two-class seat count (rough)
    notes: str = ""


# Keyed by IATA equipment code. Covers every code that appears on the routes of
# the six analysed carriers in OpenFlights, plus a few common neighbours.
AIRCRAFT_TYPES: dict[str, AircraftType] = {
    # ---- Airbus narrowbody (A320 family) ----
    "318": AircraftType("318", "Airbus A318", 2003, NARROWBODY, 107),
    "319": AircraftType("319", "Airbus A319", 1996, NARROWBODY, 124),
    "320": AircraftType("320", "Airbus A320", 1988, NARROWBODY, 150),
    "32A": AircraftType(
        "32A", "Airbus A320 (sharklets)", 1988, NARROWBODY, 150, "generic A320 code"
    ),
    "32S": AircraftType(
        "32S",
        "Airbus A320 family",
        1988,
        NARROWBODY,
        150,
        "generic A318/319/320/321 code",
    ),
    "321": AircraftType("321", "Airbus A321", 1994, NARROWBODY, 185),
    # ---- Airbus widebody ----
    "330": AircraftType("330", "Airbus A330", 1994, WIDEBODY, 277, "generic A330 code"),
    "332": AircraftType("332", "Airbus A330-200", 1998, WIDEBODY, 247),
    "333": AircraftType("333", "Airbus A330-300", 1994, WIDEBODY, 277),
    "343": AircraftType("343", "Airbus A340-300", 1993, WIDEBODY, 277),
    "346": AircraftType("346", "Airbus A340-600", 2002, WIDEBODY, 326),
    "388": AircraftType("388", "Airbus A380-800", 2007, WIDEBODY, 525),
    # ---- Boeing 737 Classic ----
    "733": AircraftType("733", "Boeing 737-300", 1984, NARROWBODY, 140),
    "734": AircraftType("734", "Boeing 737-400", 1988, NARROWBODY, 150),
    "735": AircraftType("735", "Boeing 737-500", 1990, NARROWBODY, 122),
    # ---- Boeing 737 Next Generation ----
    "737": AircraftType(
        "737", "Boeing 737-700", 1998, NARROWBODY, 143, "generic 737NG code"
    ),
    "73G": AircraftType("73G", "Boeing 737-700", 1998, NARROWBODY, 143),
    "73W": AircraftType("73W", "Boeing 737-700 (winglets)", 1998, NARROWBODY, 143),
    "738": AircraftType("738", "Boeing 737-800", 1998, NARROWBODY, 162),
    "73H": AircraftType("73H", "Boeing 737-800 (winglets)", 1998, NARROWBODY, 162),
    "739": AircraftType("739", "Boeing 737-900", 2001, NARROWBODY, 177),
    # ---- Boeing 757 ----
    "752": AircraftType("752", "Boeing 757-200", 1983, NARROWBODY, 200),
    "753": AircraftType("753", "Boeing 757-300", 1999, NARROWBODY, 243),
    "757": AircraftType(
        "757", "Boeing 757-200", 1983, NARROWBODY, 200, "generic 757 code"
    ),
    # ---- Boeing 767 ----
    "763": AircraftType("763", "Boeing 767-300", 1986, WIDEBODY, 218),
    "76W": AircraftType("76W", "Boeing 767-300ER (winglets)", 1988, WIDEBODY, 218),
    "764": AircraftType("764", "Boeing 767-400", 2000, WIDEBODY, 245),
    "767": AircraftType(
        "767", "Boeing 767-300", 1986, WIDEBODY, 218, "generic 767 code"
    ),
    # ---- Boeing 777 ----
    "772": AircraftType("772", "Boeing 777-200", 1995, WIDEBODY, 314),
    "773": AircraftType("773", "Boeing 777-300", 1998, WIDEBODY, 368),
    "77L": AircraftType("77L", "Boeing 777-200LR", 2006, WIDEBODY, 317),
    "77W": AircraftType("77W", "Boeing 777-300ER", 2004, WIDEBODY, 365),
    "777": AircraftType(
        "777", "Boeing 777-200", 1995, WIDEBODY, 314, "generic 777 code"
    ),
    # ---- Boeing 747 ----
    "744": AircraftType("744", "Boeing 747-400", 1989, WIDEBODY, 416),
    "74M": AircraftType("74M", "Boeing 747-400M Combi", 1989, WIDEBODY, 290),
    "747": AircraftType(
        "747", "Boeing 747-400", 1989, WIDEBODY, 416, "generic 747 code"
    ),
    # ---- Boeing 787 ----
    "788": AircraftType("788", "Boeing 787-8", 2011, WIDEBODY, 242),
    # ---- Airbus A340 (additional variants) ----
    "340": AircraftType("340", "Airbus A340", 1993, WIDEBODY, 277, "generic A340 code"),
    "345": AircraftType("345", "Airbus A340-500", 2003, WIDEBODY, 313),
    # ---- Boeing 717 / 737-600 ----
    "717": AircraftType("717", "Boeing 717", 1999, NARROWBODY, 106),
    "736": AircraftType("736", "Boeing 737-600", 1998, NARROWBODY, 110),
    # ---- McDonnell Douglas ----
    "M80": AircraftType(
        "M80", "McDonnell Douglas MD-80", 1980, NARROWBODY, 140, "generic MD-80 code"
    ),
    "M83": AircraftType("M83", "McDonnell Douglas MD-83", 1985, NARROWBODY, 150),
    "M88": AircraftType("M88", "McDonnell Douglas MD-88", 1987, NARROWBODY, 150),
    "M90": AircraftType("M90", "McDonnell Douglas MD-90", 1995, NARROWBODY, 158),
    "M11": AircraftType("M11", "McDonnell Douglas MD-11", 1990, WIDEBODY, 293),
    # ---- Embraer E195 ----
    "E95": AircraftType("E95", "Embraer 195", 2006, REGIONAL_JET, 108),
    # ---- Regional jets ----
    "CRJ": AircraftType(
        "CRJ", "Bombardier CRJ-200", 1992, REGIONAL_JET, 50, "generic CRJ code"
    ),
    "CR7": AircraftType("CR7", "Bombardier CRJ-700", 2001, REGIONAL_JET, 70),
    "CR9": AircraftType("CR9", "Bombardier CRJ-900", 2003, REGIONAL_JET, 90),
    "CRK": AircraftType("CRK", "Bombardier CRJ-1000", 2010, REGIONAL_JET, 100),
    "E70": AircraftType("E70", "Embraer 170", 2004, REGIONAL_JET, 76),
    "E75": AircraftType("E75", "Embraer 175", 2005, REGIONAL_JET, 88),
    "E90": AircraftType("E90", "Embraer 190", 2005, REGIONAL_JET, 100),
    "EMJ": AircraftType(
        "EMJ",
        "Embraer E-Jet (family)",
        2004,
        REGIONAL_JET,
        88,
        "generic Embraer E-Jet code",
    ),
    "ER4": AircraftType("ER4", "Embraer ERJ-145", 1996, REGIONAL_JET, 50),
    "ERJ": AircraftType(
        "ERJ",
        "Embraer ERJ (family)",
        1996,
        REGIONAL_JET,
        50,
        "generic Embraer ERJ code",
    ),
    "AR8": AircraftType("AR8", "Avro RJ85 (BAe 146)", 1993, REGIONAL_JET, 100),
    "F70": AircraftType("F70", "Fokker 70", 1994, REGIONAL_JET, 79),
    "FRJ": AircraftType(
        "FRJ",
        "Fairchild Dornier 328JET",
        1999,
        REGIONAL_JET,
        32,
        "ambiguous IATA code; best-effort mapping",
    ),
    # ---- Turboprops ----
    "AT5": AircraftType("AT5", "ATR 42-500", 1995, TURBOPROP, 48),
    "AT7": AircraftType("AT7", "ATR 72", 1989, TURBOPROP, 70),
    "DH8": AircraftType(
        "DH8", "Bombardier Dash 8", 1984, TURBOPROP, 50, "generic Dash 8 code"
    ),
    "DH4": AircraftType("DH4", "Bombardier Dash 8 Q400", 2000, TURBOPROP, 78),
    "F50": AircraftType("F50", "Fokker 50", 1987, TURBOPROP, 56),
    "J31": AircraftType("J31", "BAe Jetstream 31", 1982, TURBOPROP, 19),
    "S20": AircraftType("S20", "Saab 2000", 1994, TURBOPROP, 50),
}


def lookup(code: str) -> AircraftType | None:
    """Return the AircraftType for an IATA equipment code, or None if unknown."""
    return AIRCRAFT_TYPES.get(code.strip().upper())
