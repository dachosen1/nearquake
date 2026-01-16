import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from io import BytesIO

import requests
from PIL import Image

from nearquake.config import (EVENT_DETAIL_URL, TIMESTAMP_NOW,
                              tweet_conclusion_text)

_logger = logging.getLogger(__name__)


def extract_properties(data: dict, keylist: list):
    """
    Extracts specified properties from a data dictionary and removes specific characters.

    Given a dictionary and a list of keys, this function creates a new dictionary containing
    only the key-value pairs where the keys are in the provided list.

    Example:
    >>> extract_properties({'name': 'John, Doe', 'age': 30, 'city': 'New York'}, ['name', 'age'])
    {'name': 'JohnDoe', 'age': 30}

    :param data: The dictionary from which to extract properties
    :param keylist: A list of keys to extract from the dictionary.

    :return: dict: A dictionary containing key-value pairs for each key in keylist. String values
              are stripped of commas, single quotes, and spaces. Non-string values are
              included as-is.
    """
    table = str.maketrans("", "", ",'")
    return {
        key: (
            data.get(key, "").translate(table)
            if isinstance(data.get(key, ""), str)
            else data.get(key, "")
        )
        for key in keylist
    }


def extract_coordinates(data):
    coordinates = []
    for d in data["features"]:
        coordinates.append([d["id"], *d["geometry"]["coordinates"]])
    return coordinates


def get_earthquake_image_url(event_data):
    """
    Extract an image URL from earthquake event data, trying multiple sources.

    Tries to find an image in this priority order:
    1. Shakemap PGA (Peak Ground Acceleration) image
    2. Shakemap intensity image
    3. DYFI (Did You Feel It) intensity map
    4. DYFI response map

    Example:
        # From event data dict
        get_earthquake_image_url({"properties": {"products": {"shakemap": [...]}}})

    :param event_data: Dictionary containing earthquake event data from USGS API
    :return: String containing the URL to an image, or None if no image could be found.
    """
    try:
        products = event_data["properties"]["products"]
    except (KeyError, TypeError) as e:
        _logger.error(f"Could not find products in event data: {e}")
        return None

    # Define image sources to try in priority order
    # Each entry: (product_name, list of possible content keys)
    image_sources = [
        (
            "shakemap",
            ["download/pga.jpg", "download/intensity.jpg", "download/pga.png"],
        ),
        ("dyfi", ["dyfi_geo_10km.png", "dyfi_geo_1km.png", "dyfi_plot_atten.png"]),
    ]

    for product_name, content_keys in image_sources:
        if product_name in products:
            try:
                product_contents = products[product_name][0]["contents"]
                for content_key in content_keys:
                    if content_key in product_contents:
                        image_url = product_contents[content_key]["url"]
                        _logger.info(f"Found image from {product_name}/{content_key}")
                        return image_url
            except (KeyError, TypeError, IndexError) as e:
                _logger.debug(f"Could not extract image from {product_name}: {e}")
                continue

    _logger.warning("No image found in any USGS product for this event")
    return None


def extract_url_content(url: str) -> bytes:
    """
    Extract content from a given URL.

    :param url: The URL from which content will be extracted.
    :return: The content retrieved from the URL in binary format (bytes).
    """
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        _logger.error(
            f"Failed to get data from URL {url}. Status code: {response.status_code}"
        )
        return None

    try:
        content = response.content
        return content

    except KeyError:
        _logger.error("Could not find image URL in response data.")
        return None


def extract_image(image_data: bytes) -> Image.Image:
    """
    Extract an image from binary image data.

    :param image_data: The binary image data to be processed.
    :return: A Pillow (PIL) Image object representing the extracted image.
    """
    image_stream = BytesIO(image_data)
    image = Image.open(image_stream)
    return image


def save_content(content: bytes, content_id: str, directory: str = "image"):
    """
    save byte content into a specified directory.

    :param content_id: Identifier to be used in the image file name.
    :param directory: Directory where the image will be saved. Defaults to 'image'.
    :return: None
    """

    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{content_id}.jpg")

    try:
        with open(os.path.join(directory, f"{content_id}.jpg"), "wb") as f:
            f.write(content)
            _logger.info(f"Image downloaded and saved to {file_path}")

    except Exception as e:
        _logger.error("An error occured while writing the file: %e", e)


def fetch_json_data_from_url(url, params=None):
    """
    Fetches and loads JSON data from a specified URL.

    This function sends an HTTP GET request to the provided URL and attempts to parse
    the response as JSON.

    Note:
        This function assumes that the response is JSON. Non-JSON responses will result in a JSONDecodeError

    Example:
        >>> fetch_json_data_from_url('https://api.example.com/data')
        {'key': 'value'}

    :param url: The URL from which to fetch JSON data.
    :param params: Optional dictionary of query parameters to add to the request.

    :return: dict or None: A Python dictionary parsed from the JSON response if the request is successful and the response contains valid JSON.
    Returns None if there's an HTTP error or if the response is not valid JSON.

    """
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raise an HTTPError for bad requests (4xx or 5xx)

        try:
            return json.loads(response.text)

        except json.JSONDecodeError:
            _logger.error("Failed to decode JSON from the response.")

            return None

    except requests.exceptions.HTTPError as e:
        _logger.error(f"HTTP error occurred while fetching data: {e}")
        return None

    except requests.exceptions.ConnectionError as e:
        _logger.error(f"Connection error occurred while fetching data: {e}")
        return None

    except requests.exceptions.Timeout as e:
        _logger.error(f"Timeout error occurred while fetching data: {e}")
        return None

    except requests.exceptions.RequestException as e:
        _logger.error(f"An error occurred while fetching data: {e}")
        return None


def convert_timestamp_to_utc(timestamp: int):
    """
    Converts a given timestamp into a UTC datetime object.

    This function takes a timestamp (assumed to be in milliseconds since the Unix epoch)
    and converts it into a Python datetime object in UTC.

    :param timestamp: The timestamp to be converted. This should be an integer representing the time in milliseconds since the Unix epoch
    (00:00:00 UTC on 1 January 1970).

    Example:
        >>> convert_timestamp_to_utc(1609459200000)
        datetime.datetime(2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

    :return: datetime: A datetime object representing the given timestamp in UTC.

    """
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc)


def generate_date_range(start_date, end_date, interval) -> tuple:
    """
    Generates a list of (start_date, end_date) tuples where each tuple represents a range.
    Each range starts at 'start_date' and ends at the minimum of 'end_date' or 'start_date' + 'interval', incremented by 'interval' days.


    :param start_date: The beginning date of the range (format: 'YYYY-MM-DD').
    :param end_date: The ending date of the range (format: 'YYYY-MM-DD').
    :param interval: The number of days to increment each start date within the range.
    :return: A list of tuples, each containing a start and end date.
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    current_start_date = start_date
    date_list = []

    while current_start_date < end_date:
        current_end_date = min(end_date, current_start_date + timedelta(days=interval))
        date_list.append((current_start_date, current_end_date))
        current_start_date = current_end_date

    return date_list


def backfill_valid_date_range(start_date, end_date, interval: int) -> tuple:
    """
    Validates the date format of start and end dates, generates a range of dates
    within the specified interval, and logs the backfill process.

    :param start_date: The start date in "YYYY-MM-DD" format.
    :param end_date: The end date in "YYYY-MM-DD" format.
    :param interval: The interval in days between each date in the range

    :return: A tuple of date ranges from start_date to end_date with the specified interval
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start >= end:
            raise ValueError("start_date must be before end_date")
        if interval <= 0:
            raise ValueError("interval must be positive")

    except ValueError as err:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.") from err

    date_range = generate_date_range(start_date, end_date, interval=interval)

    _logger.info(
        f"Backfill process started for the range {start_date} to {end_date}. Running in module {__name__}."
    )
    return date_range


def create_dir(path: str):
    """
    Creates a directory if it doesn't exist.

    :param path: The path of the directory to be created.
    :return: None
    """
    try:
        os.makedirs(path, exist_ok=True)
        _logger.info(f"Directory ensured at path: {path}")
    except Exception as e:
        _logger.error(f"Failed to create directory at {path}: {e}")
        raise ValueError

    return None


def get_earthquake_emoji(magnitude: float) -> str:
    """
    Returns contextually appropriate emoji based on earthquake magnitude.

    :param magnitude: Earthquake magnitude
    :return: Emoji string
    """
    if magnitude >= 7.0:
        return "🚨"  # Critical alert
    elif magnitude >= 6.0:
        return "⚠️"  # Warning
    elif magnitude >= 5.0:
        return "📢"  # Alert
    else:
        return "🌍"  # General earth/location


def format_earthquake_alert(
    post_type: str,
    ts_event: str = None,
    duration: timedelta = None,
    id_event: str = None,
    message: str = None,
    magnitude: float = None,
    felt: int = None,
    tsunami: bool = None,
) -> dict:
    """
    Formats an alert for an earthquake event or fact.

    :param ts_event: Timestamp of the earthquake occurrence in UTC.
    :param duration: Duration since the earthquake event occurred.
    :param id_event: Unique identifier for the earthquake event.
    :param post_type: Type of post, either 'event' or 'fact'.
    :param message: Message content for fact-type posts.
    :param magnitude: Earthquake magnitude.
    :param place: Location description.
    :param felt: Number of people who reported feeling it.
    :param tsunami: Whether tsunami was generated.
    :return: A dictionary formatted as an alert or fact post.
    """

    ts_upload_utc = TIMESTAMP_NOW.strftime("%Y-%m-%d %H:%M:%S")

    if post_type == "event":
        # Get appropriate emoji
        emoji = get_earthquake_emoji(magnitude)

        # Format time ago
        minutes_ago = duration.seconds / 60
        time_str = (
            f"{minutes_ago:.0f} min ago"
            if minutes_ago < 60
            else f"{minutes_ago/60:.1f} hrs ago"
        )

        location = message.split(" - ", 1)[1] if " - " in message else message
        narrative = f"{emoji} #RecentEarthquake: A magnitude {magnitude} earthquake occurred {location} at {ts_event} UTC ({time_str})."
        # Add felt reports if available - this creates engagement!
        if felt and felt > 0:
            narrative += f"\n🙋 {felt:,} people reported feeling it!"

        # Add tsunami warning if applicable
        if tsunami:
            narrative += "\n🌊 TSUNAMI WARNING"

        # Add full details link
        narrative += f"\n\n🔗 Full details: {EVENT_DETAIL_URL.format(id=id_event)}"

        # Add engaging call-to-action or safety tip based on magnitude
        if magnitude >= 5.5:
            narrative += "\n\n💬 Did you feel it? Reply with your location! #Earthquake"
        else:
            conclusion = tweet_conclusion_text()
            # Ensure hashtags are properly formatted
            conclusion = conclusion.replace("#usgs", "#USGS")
            conclusion = conclusion.replace("#safetyfirst", "#SafetyFirst")
            conclusion = conclusion.replace("#earthquake", "#Earthquake")
            narrative += f"\n{conclusion}"

        return {
            "post": narrative,
            "ts_upload_utc": ts_upload_utc,
            "id_event": id_event,
            "post_type": post_type,
        }
    elif post_type == "fact":
        return {
            "post": message,
            "ts_upload_utc": ts_upload_utc,
            "id_event": None,
            "post_type": post_type,
        }
    else:
        raise ValueError("Invalid post type. Please choose 'event' or 'fact'.")


def convert_datetime(date: datetime, format_type: str = "date") -> str:
    """
    Convert a datetime object to a formatted string.

    :param date: The datetime object to format.
    :param format_type: The type of format to apply. Options are date or timestamp defaults to 'date'
    :return: The formatted date string.
    """
    if format_type == "date":
        return date.strftime("%Y-%m-%d")
    elif format_type == "timestamp":
        return date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError("Invalid format_type. Only 'date' or 'timestamp' are allowed.")


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = func(*args, **kwargs)
        end_ts = time.perf_counter()
        duration = end_ts - start_ts
        if duration < 60:
            value, period = duration, "seconds"
        elif duration < 3600:
            value, period = duration // 60, "minutes"
        else:
            value, period = duration // 3600, "hours"

        _logger.info(f"{func.__name__} completed in {value:.0f} {period}")
        return result

    return wrapper


def get_earthquakes_within_radius(
    conn, latitude: float, longitude: float, radius_miles: float = 5.0
):
    """
    Query all earthquakes within a specified radius of a location.
    Uses the Haversine formula to calculate distance.

    :param conn: Database session connection
    :param latitude: Latitude of the center point
    :param longitude: Longitude of the center point
    :param radius_miles: Radius in miles (default 5.0)
    :return: List of earthquakes within the radius
    """
    from sqlalchemy import func

    from nearquake.app.db import EventDetails

    # Convert miles to kilometers (Haversine formula uses km)
    radius_km = radius_miles * 1.60934

    # Query using Haversine formula to calculate distance
    # The formula calculates great-circle distance between two points on a sphere
    distance_formula = 6371 * func.acos(
        func.least(
            1.0,
            func.cos(func.radians(latitude))
            * func.cos(func.radians(EventDetails.latitude))
            * func.cos(func.radians(EventDetails.longitude) - func.radians(longitude))
            + func.sin(func.radians(latitude))
            * func.sin(func.radians(EventDetails.latitude)),
        )
    )

    query = (
        conn.session.query(
            EventDetails.id_event,
            EventDetails.mag,
            EventDetails.ts_event_utc,
            EventDetails.place,
            EventDetails.latitude,
            EventDetails.longitude,
            distance_formula.label("distance_km"),
        )
        .filter(
            EventDetails.type == "earthquake",
            EventDetails.mag.isnot(None),
            distance_formula <= radius_km,
        )
        .order_by(EventDetails.ts_event_utc.desc())
    )

    try:
        results = query.all()
        _logger.info(
            f"Found {len(results)} earthquakes within {radius_miles} miles of the earthquake"
        )
        return results
    except Exception as e:
        _logger.error(f"Error querying earthquakes within radius: {e}")
        return []


def get_earthquake_statistics(
    conn, latitude: float, longitude: float, current_magnitude: float
) -> dict:
    """
    Get comprehensive earthquake statistics for a region to provide context.

    :param conn: Database session connection
    :param latitude: Latitude of the earthquake
    :param longitude: Longitude of the earthquake
    :param current_magnitude: Magnitude of the current earthquake
    :return: Dictionary with regional statistics
    """
    from sqlalchemy import func

    from nearquake.app.db import EventDetails

    stats = {
        "total_5yr": 0,
        "total_1yr": 0,
        "largest_mag": None,
        "largest_date": None,
        "largest_place": None,
        "avg_per_year": 0,
        "similar_or_larger_count": 0,
        "last_similar_date": None,
        "last_similar_mag": None,
        "recent_30d_count": 0,
    }

    # Use 150-mile radius for regional context (about 240 km)
    radius_km = 150 * 1.60934

    distance_formula = 6371 * func.acos(
        func.least(
            1.0,
            func.cos(func.radians(latitude))
            * func.cos(func.radians(EventDetails.latitude))
            * func.cos(func.radians(EventDetails.longitude) - func.radians(longitude))
            + func.sin(func.radians(latitude))
            * func.sin(func.radians(EventDetails.latitude)),
        )
    )

    try:
        now = datetime.now(timezone.utc)
        five_years_ago = now - timedelta(days=5 * 365)
        one_year_ago = now - timedelta(days=365)
        thirty_days_ago = now - timedelta(days=30)

        # Total earthquakes in last 5 years (M4.5+)
        total_5yr = (
            conn.session.query(func.count(EventDetails.id_event))
            .filter(
                EventDetails.type == "earthquake",
                EventDetails.mag >= 4.5,
                EventDetails.ts_event_utc >= five_years_ago,
                distance_formula <= radius_km,
            )
            .scalar()
            or 0
        )
        stats["total_5yr"] = total_5yr
        stats["avg_per_year"] = round(total_5yr / 5, 1) if total_5yr > 0 else 0

        # Total in last year
        stats["total_1yr"] = (
            conn.session.query(func.count(EventDetails.id_event))
            .filter(
                EventDetails.type == "earthquake",
                EventDetails.mag >= 4.5,
                EventDetails.ts_event_utc >= one_year_ago,
                distance_formula <= radius_km,
            )
            .scalar()
            or 0
        )

        # Recent activity (last 30 days)
        stats["recent_30d_count"] = (
            conn.session.query(func.count(EventDetails.id_event))
            .filter(
                EventDetails.type == "earthquake",
                EventDetails.mag >= 4.5,
                EventDetails.ts_event_utc >= thirty_days_ago,
                distance_formula <= radius_km,
            )
            .scalar()
            or 0
        )

        # Largest earthquake in region (all time in our database)
        largest = (
            conn.session.query(
                EventDetails.mag,
                EventDetails.ts_event_utc,
                EventDetails.place,
            )
            .filter(
                EventDetails.type == "earthquake",
                EventDetails.mag.isnot(None),
                distance_formula <= radius_km,
            )
            .order_by(EventDetails.mag.desc())
            .first()
        )
        if largest:
            stats["largest_mag"] = largest.mag
            stats["largest_date"] = largest.ts_event_utc
            stats["largest_place"] = largest.place

        # Count of earthquakes similar magnitude or larger (within 0.5)
        similar_threshold = current_magnitude - 0.5
        similar_quakes = (
            conn.session.query(
                EventDetails.mag,
                EventDetails.ts_event_utc,
            )
            .filter(
                EventDetails.type == "earthquake",
                EventDetails.mag >= similar_threshold,
                EventDetails.ts_event_utc >= five_years_ago,
                distance_formula <= radius_km,
            )
            .order_by(EventDetails.ts_event_utc.desc())
            .all()
        )
        # Exclude the current event (most recent)
        if similar_quakes and len(similar_quakes) > 1:
            stats["similar_or_larger_count"] = len(similar_quakes) - 1
            stats["last_similar_date"] = similar_quakes[1].ts_event_utc
            stats["last_similar_mag"] = similar_quakes[1].mag

        _logger.info(f"Retrieved earthquake statistics for region: {stats}")
        return stats

    except Exception as e:
        _logger.error(f"Error getting earthquake statistics: {e}")
        return stats


def get_recent_context_posts(conn, limit: int = 5) -> list:
    """
    Get recent context posts from database to help LLM avoid repetition.

    :param conn: Database session connection
    :param limit: Number of recent posts to retrieve
    :return: List of recent context post texts
    """
    from nearquake.app.db import Post

    try:
        recent_posts = (
            conn.session.query(Post.post)
            .filter(Post.post_type == "context")
            .order_by(Post.ts_upload_utc.desc())
            .limit(limit)
            .all()
        )
        return [p.post for p in recent_posts if p.post]
    except Exception as e:
        _logger.error(f"Error fetching recent context posts: {e}")
        return []


def generate_earthquake_context(
    magnitude: float,
    location: str,
    latitude: float = None,
    longitude: float = None,
    conn=None,
) -> str:
    """
    Generate historical context for a significant earthquake using OpenAI.

    :param magnitude: Earthquake magnitude
    :param location: Location description
    :param latitude: Latitude of the earthquake (optional, for querying nearby events)
    :param longitude: Longitude of the earthquake (optional, for querying nearby events)
    :param conn: Database connection (optional, for querying historical data)
    :return: Context text suitable for a tweet (220 chars or less, accounting for prefix)
    """
    from nearquake.open_ai_client import generate_response

    # Character limit: Twitter max 280 - "📊 Context: " prefix (13 chars) = 267
    # Use 220 for safety margin since LLMs often overshoot
    MAX_CHARS = 220

    stats_str = ""
    recent_posts_str = ""

    if latitude is not None and longitude is not None and conn is not None:
        try:
            # Get comprehensive regional statistics
            stats = get_earthquake_statistics(conn, latitude, longitude, magnitude)

            stats_str = f"""
REGIONAL EARTHQUAKE DATA (within 150 miles):
- Total M4.5+ earthquakes in last 5 years: {stats['total_5yr']}
- Average per year: {stats['avg_per_year']}
- Total in last 12 months: {stats['total_1yr']}
- Recent activity (last 30 days): {stats['recent_30d_count']} earthquakes"""

            if stats["largest_mag"]:
                stats_str += f"""
- Largest recorded in region: M{stats['largest_mag']:.1f} on {stats['largest_date'].strftime('%Y-%m-%d') if stats['largest_date'] else 'unknown'}"""

            if stats["similar_or_larger_count"] > 0:
                stats_str += f"""
- Similar magnitude (M{magnitude - 0.5:.1f}+) in last 5 years: {stats['similar_or_larger_count']} events"""
                if stats["last_similar_date"]:
                    stats_str += f"""
- Most recent similar: M{stats['last_similar_mag']:.1f} on {stats['last_similar_date'].strftime('%Y-%m-%d')}"""

            # Get recent context posts to avoid repetition
            recent_posts = get_recent_context_posts(conn, limit=3)
            if recent_posts:
                recent_posts_str = (
                    "\n\nRECENT CONTEXT TWEETS (avoid similar phrasing):\n"
                )
                for post in recent_posts:
                    recent_posts_str += f'- "{post[:100]}..."\n'

        except Exception as e:
            _logger.error(f"Failed to fetch earthquake statistics: {e}")

    prompt = f"""Write a compelling 1-2 sentence context tweet ({MAX_CHARS} chars MAX) about a M{magnitude} quake near {location}.
{stats_str}
{recent_posts_str}
Choose the MOST SURPRISING or NEWSWORTHY angle from the data:
- "First M5+ here since [date]" or "3rd major quake this month" (rarity/frequency)
- "Region averages X quakes/year, already had Y this year" (trend)
- "Largest here was M6.8 in 2019 - today's is the biggest since" (historical comparison)
- "This fault line has been unusually quiet/active lately" (pattern)

STRICT RULES:
- MAXIMUM {MAX_CHARS} characters (count carefully!)
- Lead with the most interesting fact
- Use specific numbers from the data
- No hashtags, emojis, or quotes
- Sound like an informed seismologist, not a textbook"""

    try:
        response = generate_response(prompt=prompt, role="user", model="gpt-5.0")
        # Clean up response
        response = response.strip().strip('"').strip("'")
        # Truncate if needed (should rarely happen with good prompt)
        if len(response) > MAX_CHARS:
            # Try to truncate at sentence boundary
            truncated = response[:MAX_CHARS]
            last_period = truncated.rfind(".")
            if last_period > MAX_CHARS - 50:
                response = truncated[: last_period + 1]
            else:
                response = truncated[: MAX_CHARS - 3] + "..."
        return response
    except Exception as e:
        _logger.error(f"Failed to generate earthquake context: {e}")
        return f"The area within 150 miles sees an average of several M4.5+ quakes yearly. Seismic activity here is worth monitoring."


def generate_preparedness_tip() -> str:
    """
    Generate a preparedness tip using OpenAI.

    :return: Preparedness tip text suitable for a tweet (280 chars or less)
    """
    from nearquake.open_ai_client import generate_response

    prompt = """Generate a brief earthquake preparedness tip (max 250 characters).

Focus on ONE actionable tip such as:
- What to do during shaking
- Emergency kit essentials
- Home safety measures
- Community preparedness

Keep it concise and actionable. Do NOT include quotes or excessive hashtags. Include 1-2 relevant emojis. This will be the final tweet in a 3-tweet thread."""

    try:
        response = generate_response(prompt=prompt, role="user", model="gpt-5.0")
        # Truncate if needed
        if len(response) > 250:
            response = response[:247] + "..."
        return response
    except Exception as e:
        _logger.error(f"Failed to generate preparedness tip: {e}")
        return "🏠 Secure heavy items to walls and practice Drop, Cover, and Hold On with your family. Being prepared saves lives! #EarthquakePrep"
