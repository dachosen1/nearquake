EARTH_QUAKE_FEATURES = (
    "ids",
    "mag",
    "place",
    "time",
    "updated",
    "tz",
    "felt",
    "cdi",
    "mmi",
    "alert",
    "status",
    "tsunami",
    "type",
    "title",
)

API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

EARTHQUAKE_URL_TEMPLATE = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31"

def generate_earthquake_url(year, month, url_template= EARTHQUAKE_URL_TEMPLATE):
    """
    Generate the URL for extracting earthquakes that occurred during a specific year and month.
    :param year: Year
    :param month: Month
    :param url_template: URL template string that includes placeholders for 'year' and 'month',
                        defaults to EARTHQUAKE_URL_TEMPLATE
    :return: The URL path for the earthquakes that happened during the specified month and year.
    """
    return url_template.format(year=year, month=month)
