import argparse


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Nearquake Data Processor")
    parser.add_argument(
        "-d", "--daily", action="store_true", help="Execute the daily program"
    )
    parser.add_argument(
        "-l",
        "--live",
        action="store_true",
        help="Periodically check for new earthquakes",
    )
    parser.add_argument(
        "-i",
        "--initialize",
        action="store_true",
        help="Initialize all required databases",
    )
    parser.add_argument(
        "-w", "--weekly", action="store_true", help="Execute the weekly program"
    )
    parser.add_argument(
        "-m", "--monthly", action="store_true", help="Execute the monthly program"
    )
    parser.add_argument(
        "-f", "--fun", action="store_true", help="Tells a fun fact about earthquakes"
    )
    parser.add_argument(
        "-b",
        "--backfill",
        action="store_true",
        help="backfill database using a date range",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for backfill (required with --backfill)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for backfill (required with --backfill)",
    )
    parser.add_argument(
        "--backfill-events",
        action="store_true",
        help="Backfill earthquake event details",
    )
    parser.add_argument(
        "--backfill-locations",
        action="store_true",
        help="Backfill earthquake location data",
    )
    return parser.parse_args()
