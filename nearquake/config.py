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

_custom_date_ = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31"

def generate_custom_date_url(year, month, _custom_date_= _custom_date_):
    return _custom_date_.format(year=year, month=month)
