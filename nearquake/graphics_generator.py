"""
Professional earthquake summary graphics generator.
Clean, simple, and elegant design for social media.
"""

import io
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

from nearquake.app.db import EventDetails
from nearquake.utils.logging_utils import get_logger, log_info

_logger = get_logger(__name__)

# Elegant dark theme color palette
COLORS = {
    "bg": "#1a1a1a",  # Dark background
    "card_bg": "#2a2a2a",  # Card background
    "primary": "#4CAF50",  # Green
    "accent": "#2196F3",  # Blue accent
    "text": "#FFFFFF",  # White text
    "text_light": "#B0B0B0",  # Gray text
    "grid": "#404040",  # Dark grid
    "bar_colors": [
        "#4CAF50",
        "#8BC34A",
        "#FFC107",
        "#FF9800",
        "#F44336",
    ],  # Green to red gradient
}


def generate_daily_summary_graphic(
    conn, date: str = None, output_path: str = None
) -> bytes:
    """
    Generate a professional daily earthquake summary graphic.

    :param conn: Database connection
    :param date: Date in YYYY-MM-DD format (defaults to yesterday)
    :param output_path: Optional path to save the image
    :return: Image data as bytes
    """
    if date is None:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    log_info(_logger, f"Generating daily summary graphic for {date}")

    # Query earthquakes for the day
    events = (
        conn.session.query(EventDetails)
        .filter(EventDetails.date == date, EventDetails.type == "earthquake")
        .all()
    )

    if not events:
        log_info(_logger, f"No earthquakes found for {date}")
        return None

    # Set style for professional look
    plt.style.use("seaborn-v0_8-whitegrid")

    # Prepare data
    magnitudes = [e.mag for e in events if e.mag]
    total_count = len(events)
    max_mag = max(magnitudes) if magnitudes else 0
    max_mag_event = max(events, key=lambda e: e.mag if e.mag else 0)

    # Create figure with title
    fig = plt.figure(figsize=(12, 7), facecolor=COLORS["bg"])

    # Add simple chart title
    fig.suptitle(
        f"Daily Earthquake Summary - {date}",
        fontsize=24,
        fontweight="700",
        color=COLORS["text"],
        x=0.5,
        y=0.96,
    )

    gs = fig.add_gridspec(1, 2, width_ratios=[4.5, 1], wspace=0.2)

    # Prepare magnitude bins
    mag_bins = [0, 2.5, 4.0, 5.0, 6.0, 10.0]
    mag_labels = ["<2.5", "2.5-4.0", "4.0-5.0", "5.0-6.0", "6.0+"]
    mag_counts = np.histogram(magnitudes, bins=mag_bins)[0]

    # Left: Bar chart
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(COLORS["bg"])

    bars = ax1.bar(
        mag_labels,
        mag_counts,
        color=COLORS["bar_colors"],
        edgecolor="none",
        alpha=0.9,
        width=0.6,
    )

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=15,
                fontweight="600",
                color=COLORS["text"],
            )

    ax1.set_xlabel(
        "Magnitude Range",
        fontsize=16,
        color=COLORS["text"],
        fontweight="500",
        labelpad=10,
    )
    ax1.set_ylabel(
        "Earthquakes", fontsize=16, color=COLORS["text"], fontweight="500", labelpad=10
    )
    ax1.tick_params(colors=COLORS["text_light"], labelsize=14)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(COLORS["grid"])
    ax1.spines["bottom"].set_color(COLORS["grid"])
    ax1.grid(axis="y", alpha=0.3, color=COLORS["grid"], linestyle=":", linewidth=0.8)
    ax1.set_axisbelow(True)

    # Right: Statistics
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")

    # Format location for stats panel
    location_short = max_mag_event.place if max_mag_event.place else "Unknown"
    if len(location_short) > 40:
        location_short = location_short[:37] + "..."

    # Position statistics higher on the panel
    stats_y = 0.91
    line_height = 0.25

    # Total events
    ax2.text(
        0.1,
        stats_y,
        "Total Earthquakes",
        fontsize=15,
        color=COLORS["text_light"],
        fontweight="500",
    )
    ax2.text(
        0.1,
        stats_y - 0.13,
        f"{total_count:,}",
        fontsize=43,
        fontweight="700",
        color=COLORS["primary"],
    )
    stats_y -= line_height * 1.6

    # Largest quake
    ax2.text(
        0.1,
        stats_y,
        "Largest Earthquake",
        fontsize=15,
        color=COLORS["text_light"],
        fontweight="500",
    )
    ax2.text(
        0.1,
        stats_y - 0.13,
        f"M{max_mag:.1f}",
        fontsize=38,
        fontweight="700",
        color=COLORS["accent"],
    )
    ax2.text(
        0.1,
        stats_y - 0.24,
        location_short,
        fontsize=14,
        color=COLORS["text_light"],
        style="italic",
        wrap=True,
    )

    # Footer
    fig.text(
        0.98,
        0.02,
        "Data: USGS | @quakebot_",
        ha="right",
        fontsize=8,
        color=COLORS["text_light"],
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(
        buf,
        format="png",
        facecolor=COLORS["bg"],
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.3,
    )
    buf.seek(0)
    image_data = buf.read()
    plt.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(image_data)
        log_info(_logger, f"Saved daily summary graphic to {output_path}")

    log_info(_logger, f"Generated daily summary graphic for {date}")
    return image_data


def generate_weekly_summary_graphic(
    conn, end_date: str = None, output_path: str = None
) -> bytes:
    """
    Generate a professional weekly earthquake summary graphic.

    :param conn: Database connection
    :param end_date: End date in YYYY-MM-DD format (defaults to yesterday)
    :param output_path: Optional path to save the image
    :return: Image data as bytes
    """
    if end_date is None:
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=6)).strftime(
        "%Y-%m-%d"
    )

    log_info(
        _logger, f"Generating weekly summary graphic from {start_date} to {end_date}"
    )

    # Query earthquakes for the week
    events = (
        conn.session.query(EventDetails)
        .filter(
            EventDetails.date >= start_date,
            EventDetails.date <= end_date,
            EventDetails.type == "earthquake",
        )
        .all()
    )

    if not events:
        log_info(_logger, f"No earthquakes found for week ending {end_date}")
        return None

    # Set style
    plt.style.use("seaborn-v0_8-whitegrid")

    # Prepare summary data
    magnitudes = [e.mag for e in events if e.mag]
    total_count = len(events)
    max_mag = max(magnitudes) if magnitudes else 0
    max_mag_event = max(events, key=lambda e: e.mag if e.mag else 0)

    # Create figure with title
    fig = plt.figure(figsize=(12, 8.5), facecolor=COLORS["bg"])

    # Add simple chart title
    start_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%b %d")
    end_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%b %d, %Y")
    fig.suptitle(
        f"Weekly Earthquake Summary - {start_fmt} to {end_fmt}",
        fontsize=24,
        fontweight="700",
        color=COLORS["text"],
        x=0.5,
        y=0.96,
    )

    gs = fig.add_gridspec(
        2, 2, height_ratios=[1, 1], width_ratios=[4.5, 1], hspace=0.3, wspace=0.2
    )

    # Prepare data by day
    dates = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    while current_date <= datetime.strptime(end_date, "%Y-%m-%d"):
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    daily_counts = []
    for date in dates:
        day_events = [e for e in events if e.date.strftime("%Y-%m-%d") == date]
        daily_counts.append(len(day_events))

    # Top left: Daily trend line
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(COLORS["bg"])

    day_labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%m/%d") for d in dates]

    ax1.plot(
        day_labels,
        daily_counts,
        marker="o",
        linewidth=2.5,
        markersize=8,
        color=COLORS["primary"],
        markerfacecolor=COLORS["accent"],
        markeredgewidth=0,
    )
    ax1.fill_between(
        range(len(day_labels)), daily_counts, alpha=0.15, color=COLORS["primary"]
    )

    ax1.set_ylabel(
        "Daily Earthquakes",
        fontsize=16,
        color=COLORS["text"],
        fontweight="500",
        labelpad=10,
    )
    ax1.tick_params(colors=COLORS["text_light"], labelsize=14)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(COLORS["grid"])
    ax1.spines["bottom"].set_color(COLORS["grid"])
    ax1.grid(axis="y", alpha=0.3, color=COLORS["grid"], linestyle=":", linewidth=0.8)
    ax1.set_axisbelow(True)

    # Bottom left: Magnitude distribution
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_facecolor(COLORS["bg"])

    mag_bins = [0, 2.5, 4.0, 5.0, 6.0, 10.0]
    mag_labels = ["<2.5", "2.5-4.0", "4.0-5.0", "5.0-6.0", "6.0+"]
    mag_counts = np.histogram(magnitudes, bins=mag_bins)[0]

    bars = ax2.bar(
        mag_labels,
        mag_counts,
        color=COLORS["bar_colors"],
        edgecolor="none",
        alpha=0.9,
        width=0.6,
    )

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=14,
                fontweight="600",
                color=COLORS["text"],
            )

    ax2.set_xlabel(
        "Magnitude Range",
        fontsize=14,
        color=COLORS["text"],
        fontweight="500",
        labelpad=8,
    )
    ax2.set_ylabel(
        "Earthquakes", fontsize=14, color=COLORS["text"], fontweight="500", labelpad=8
    )
    ax2.tick_params(colors=COLORS["text_light"], labelsize=12)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_color(COLORS["grid"])
    ax2.spines["bottom"].set_color(COLORS["grid"])
    ax2.grid(axis="y", alpha=0.3, color=COLORS["grid"], linestyle=":", linewidth=0.8)
    ax2.set_axisbelow(True)

    # Right: Statistics spanning both rows
    ax3 = fig.add_subplot(gs[:, 1])
    ax3.axis("off")

    # Format location for stats panel
    location_short = max_mag_event.place if max_mag_event.place else "Unknown"
    if len(location_short) > 40:
        location_short = location_short[:37] + "..."

    # Position statistics higher on the panel
    stats_y = 0.73
    line_height = 0.20

    # Total events
    ax3.text(
        0.1,
        stats_y,
        "Total Earthquakes",
        fontsize=15,
        color=COLORS["text_light"],
        fontweight="500",
    )
    ax3.text(
        0.1,
        stats_y - 0.10,
        f"{total_count:,}",
        fontsize=43,
        fontweight="700",
        color=COLORS["primary"],
    )
    stats_y -= line_height * 1.6

    # Largest quake
    ax3.text(
        0.1,
        stats_y,
        "Largest Earthquake",
        fontsize=15,
        color=COLORS["text_light"],
        fontweight="500",
    )
    ax3.text(
        0.1,
        stats_y - 0.10,
        f"M{max_mag:.1f}",
        fontsize=38,
        fontweight="700",
        color=COLORS["accent"],
    )
    ax3.text(
        0.1,
        stats_y - 0.18,
        location_short,
        fontsize=14,
        color=COLORS["text_light"],
        style="italic",
        wrap=True,
    )

    # Footer
    fig.text(
        0.98,
        0.02,
        "Data: USGS | @quakebot_",
        ha="right",
        fontsize=8,
        color=COLORS["text_light"],
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(
        buf,
        format="png",
        facecolor=COLORS["bg"],
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.3,
    )
    buf.seek(0)
    image_data = buf.read()
    plt.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(image_data)
        log_info(_logger, f"Saved weekly summary graphic to {output_path}")

    log_info(_logger, f"Generated weekly summary graphic for week ending {end_date}")
    return image_data
