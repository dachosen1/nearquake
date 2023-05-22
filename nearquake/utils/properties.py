

def extract_properties(data, keylist):
    table = str.maketrans('', '', ",'")
    return {
        key: (data.get(key, '').translate(table) 
              if isinstance(data.get(key, ''), str) 
              else data.get(key, ''))
        for key in keylist
    }

def get_image_url(response):
    try:
        return response['properties']['products']['shakemap'][0]['contents']['download/pga.jpg']['url']
    except KeyError:
        return None

def download_image(url, id_, directory='image'):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(directory, exist_ok=True) 
        with open(os.path.join(directory, f'{id_}.jpg'), 'wb') as f:
            f.write(response.content)

def extract_coordinates(data): 
    coordinates = []
    for d in data['features']:
        coordinates.append([d['id'], *d['geometry']['coordinates']])
    return coordinates