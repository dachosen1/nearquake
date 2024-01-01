from nearquake.utils import generate_date_range

import pytest


def test_generate_date_range():
    assert generate_date_range(start_date="2023-01-01", end_date="2023-02-01") == [
        [2023, 1],
        [2023, 2],
    ]
    assert generate_date_range(start_date="2010-01-01", end_date="2010-01-01") == [
        [2010, 1],
    ]


def test_generate_date_range_value_error():
    with pytest.raises(ValueError):
        generate_date_range(start_date="2023-01-01", end_date="2022-01-01")
