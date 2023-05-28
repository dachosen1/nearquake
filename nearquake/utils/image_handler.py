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


def download_image(url, id_, directory='image'):
    """
    Downloads an image from a given URL and saves it into a specified directory.
    
    :param url: URL of the image to download.
    :param id_: Identifier to be used in the image file name.
    :param directory: Directory where the image will be saved. Defaults to 'image'.
    :return: None
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
        return
    
    os.makedirs(directory, exist_ok=True) 

    try:
        with open(os.path.join(directory, f'{id_}.jpg'), 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"An error occurred while writing the file: {e}")
