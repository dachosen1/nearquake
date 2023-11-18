from dataclasses import dataclass


class Config:
    def __init__(self) -> None:
        self.EARTH_QUAKE_FEATURES = (
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

        self.API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time}.geojson"

        self.EARTHQUAKE_URL_TEMPLATE = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31"

    @dataclass
    def generate_earthquake_url(year, month):
        """
        Generate the URL for extracting earthquakes that occurred during a specific year and month.
        :param year: Year
        :param month: Month
        :return: The URL path for the earthquakes that happened during the specified month and year.
        """
        return Config.EARTHQUAKE_URL_TEMPLATE.format(year=year, month=month)
