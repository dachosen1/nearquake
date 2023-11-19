from nearquake.config import QuakeConfig

def test_generate_earthquake_url():
    year = 2021
    month = 5
    expected_url = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime=2021-5-01%2000:00:00&endtime=2021-5-31"
    assert QuakeConfig.generate_earthquake_url(year, month) == expected_url


if __name__ == "__main__":
    from nearquake.config import QuakeConfig
    