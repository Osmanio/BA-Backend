'''
Caution: When fetching images from HTTP/HTTPS URLs, Google cannot guarantee that the request will be completed.
Your request may fail if the specified host denies the request (for example, due to request throttling or DOS prevention),
or if Google throttles requests to the site for abuse prevention. You should not depend on externally-hosted images for production applications.
'''
import json
from modules.MongoDB import mongodb_connect

import configparser
import sys
from pathlib import Path

#CONFIGURATION
ROOT_DIR = sys.path[1]
CONFIG_FILE = Path(ROOT_DIR) / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)


CONFIG_JSON_PATH = config['source_files']['json']
CONFIG_JSON_REVERSE_IMAGES_PATH = config['source_files']['json_reverse_images']

#Initilaize the connection and store it in CONSTANTS
CONNECTION = mongodb_connect.initialize_connection()
DATABASE = CONNECTION.get('DATABASE')
CLIENT = CONNECTION.get('CLIENT')
COLLECTION = CONNECTION.get('COLLECTION')

#Here we use ImageHash as ID

from PIL import Image
import hashlib


def detect_web_uri(uri, id):
    data = {}
    """Detects web annotations in the file located in Google Cloud Storage."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    image = vision.types.Image()
    image.source.image_uri = uri

    response = client.web_detection(image=image)
    annotations = response.web_detection


    if annotations.best_guess_labels:
        for label in annotations.best_guess_labels:

            print('\nBest guess label: {}'.format(label.label))
            query = {"_id": id}
            update = {"$set": {"BestGuessedLabel": label.label}}
            COLLECTION.update_one(query, update, upsert=True)
    else:
        print('No best guessed label')

    print('BEFORE IF')
    if annotations.pages_with_matching_images:
        print('We have pages with matching images')
        print('\n{} Pages with matching images found:'.format(
            len(annotations.pages_with_matching_images)))

        for page in annotations.pages_with_matching_images:
            print('\n\tPage url   : {}'.format(page.url))

            if page.full_matching_images:
                print('\t{} Full Matches found: '.format(
                    len(page.full_matching_images)))

                for image in page.full_matching_images:

                    print(image.url, 'ABA')

                    with open(Path(CONFIG_JSON_REVERSE_IMAGES_PATH)) as f:
                        data = json.load(f)
                        # We need to assign the ID
                        data['ImageURL'] = uri
                        data['ReverseImageURL'] = image.url
                        data['ReverseImagePageURL'] = page.url
                        data['ReverseImageMatchType'] = 'Full'

                    print(data)
                    query = {"_id": id}
                    update = {"$push": {"ReverseImagesMetadata": data}}
                    COLLECTION.update_one(query, update)

                    print('Image url  : {}'.format(image.url))
            elif page.partial_matching_images:
                print('\t{} Partial Matches found: '.format(
                    len(page.partial_matching_images)))

                for image in page.partial_matching_images:
                    print('\t\tImage url  : {}'.format(image.url))
                    with open(Path(CONFIG_JSON_REVERSE_IMAGES_PATH)) as f:
                        data = json.load(f)
                        # We need to assign the ID
                        data['ReverseImageURL'] = image.url
                        data['ReverseImagePageURL'] = page.url
                        data['ReverseImageMatchType'] = 'Partial'

                    print(data)
                    query = {"_id": id}
                    update = {"$push": {"ReverseImagesMetadata": data}}
                    COLLECTION.update_one(query, update)
            else:
                print('KEINE TREFFER')
    else:
        print('No images found')


    if annotations.web_entities:
        print('\n{} Web entities found: '.format(
            len(annotations.web_entities)))

        entity_storage = []
        for entity in annotations.web_entities:
            print('\n\tScore      : {}'.format(entity.score))
            print(u'\tDescription: {}'.format(entity.description))
            entity_storage.append([entity.score, entity.description])
            query = {"_id": id}
            update = {"$set": {"WebEntities": entity_storage}}
            COLLECTION.update_one(query, update)
    else:
        print('No web entities found')


    if annotations.visually_similar_images:
        print('\n{} visually similar images found:\n'.format(
            len(annotations.visually_similar_images)))

        for image in annotations.visually_similar_images:
            print('\tImage url    : {}'.format(image.url))


    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)



from modules.image_hash import average_hash as average_hash

#This method is runned if you call this component
def main(uri):
    print('START: Google API Detect Web Entities And Pages Remote')

    hash = str(average_hash(uri))
    print('The hash of the given image :', hash)

    # We check first if the image already exists in our database
    if (COLLECTION.find_one({"_id": hash})):
        # If the document already exists return False
        return hash, True
    else:
        print('Image with the hash ' + str(hash) + ' is not in the database.')

        import json
        with open(Path(CONFIG_JSON_PATH)) as f:
            data = json.load(f)
            #We need to assign the ID
            data['_id'] = hash
            data['ImageHash'] = hash
            data['ImageURL'] = uri

        COLLECTION.insert_one(data)

        #md5hash here is our unique ID in this case
        detect_web_uri(uri, hash)
        return hash, False
    print('END: Google API Detect Web Entities And Pages Remote')

#If accessed directly exit
if __name__ == '__main__':
    exit()