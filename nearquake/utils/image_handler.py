import request

def get_quake_image_url(url):
    """
    Extract the image URL from the results of the USA.gov earthquake API

    :param url: URL to the earthquake data.
    :return: String containing the URL to the image, or None if no image could be found.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to get data from URL {url}. Status code: {response.status_code}")
        return None

    try:
        data = json.loads(response.text)
        image_url = data['properties']['products']['shakemap'][0]['contents']['download/pga.jpg']['url']
        return image_url
    except KeyError:
        print("Could not find image URL in response data.")
        return None


def download_image(url, id_, directory="image"):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, f"{id_}.jpg"), "wb") as f:
            f.write(response.content)
