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
    return parser.parse_args()
