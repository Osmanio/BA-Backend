import json
from modules.MongoDB import mongodb_connect

#Initilaize the connection and store it in CONSTANTS
CONNECTION = mongodb_connect.initialize_connection()
DATABASE = CONNECTION.get('DATABASE')
CLIENT = CONNECTION.get('CLIENT')
COLLECTION = CONNECTION.get('COLLECTION')

#Here we use ImageHash as ID

from PIL import Image
import hashlib

def detect_web(path, id):
    data = {}
    data['image_url'] = []#[path]
    """Detects web annotations given an image."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

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

                    with open(r'C:\Users\Osman\PycharmProjects\CompanionBackend\source\DATAFORMAT_REVERSE_IMAGES.JSON') as f:
                        data = json.load(f)
                        # We need to assign the ID
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
                    with open(r'C:\Users\Osman\PycharmProjects\CompanionBackend\source\DATAFORMAT_REVERSE_IMAGES.JSON') as f:
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

#This method is runned if you call this component
def main(path):
    print('MAIN1')

    md5hash = hashlib.md5(Image.open(path).tobytes()).hexdigest()
    print('The MD5HASH of the given image file :', md5hash)

    # We check first if the image already exists in our database
    if (COLLECTION.find_one({"_id": md5hash})):
        # If the document already exists return False
        return md5hash
    else:
        print('MACH WEITER')

        import json
        with open(r'C:\Users\Osman\PycharmProjects\CompanionBackend\source\DATAFORMAT.JSON') as f:
            data = json.load(f)
            #We need to assign the ID
            data['_id'] = md5hash
            data['ImageHash'] = md5hash

        COLLECTION.insert_one(data)

        #md5hash here is our unique ID in this case
        detect_web(path, md5hash)
        return md5hash
    print('ENDE MAIN')

#If accessed directly exit
if __name__ == '__main__':
    exit()