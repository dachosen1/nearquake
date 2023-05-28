import os
import requests


def extract_properties(data, keylist):
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
