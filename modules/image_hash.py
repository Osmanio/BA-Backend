from PIL import Image
import imagehash
import requests

def average_hash(url):
    try:
        image_url = url
        image = Image.open(requests.get(image_url, stream=True).raw)
        hash = imagehash.average_hash(image)
    except Exception as e:
        print(e)
        #Catch the Exception
        return "ERROR"
    return hash