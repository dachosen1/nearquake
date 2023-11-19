from dataclasses import dataclass
import os


@dataclass
class QuakeConfig:
    EARTH_QUAKE_FEATURES: tuple = (
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

    API_URL: str = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_{time}.geojson"
    )

    EARTHQUAKE_URL_TEMPLATE: str = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={year}-{month}-01%2000:00:00&endtime={year}-{month}-31"

    @staticmethod
    def generate_earthquake_url(year: int, month: int) -> str:
        """
        Generate the URL for extracting earthquakes that occurred during a specific year and month.

        :param year: Year
        :param month: Month
        :return: The URL path for the earthquakes that happened during the specified month and year.
        """
        return QuakeConfig.EARTHQUAKE_URL_TEMPLATE.format(year=year, month=month)


@dataclass
class ConnectionConfig:
    user = os.environ.get("NEARQUAKE_USERNAME")
    host = os.environ.get("NEARQUAKE_HOST")
    dbname = os.environ.get("NEARQUAKE_DATABASE")
    port = os.environ.get("NEARQUAKE_PORT")
    password = os.environ.get("NEARQUAKE_PASSWORD")

    def generate_connection_url(self, sqlengine):
        if sqlengine is None: 
            raise ValueError("SQL Engine is not specifed")
        return f"{sqlengine}://{self.user}:{self.password}@{self.port}:{self.port}/{self.dbname}"

if __name__ == '__main__': 
    config = ConnectionConfig()
    config.generate_connection_url('postgresql')