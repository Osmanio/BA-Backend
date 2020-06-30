def detect_text_uri(uri):
    """
    Detects text in the file located in Google Cloud Storage or on the Web.
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    image = vision.types.Image()
    image.source.image_uri = uri

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')

    #We just need the first element, because it contains every single keyword splitted by \n
    #If there is no text it will return None
    for text in texts:
        print(text.description)
        print(type(text.description))
        #We replace the /n with an empty space to split it by the empty space and convert it to a list which we will return
        return text.description.replace('\n',' ').split()

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

def main(path):
    print('Main START google_api_optical_character_recognition_remote.py')
    return detect_text_uri(path)
    print('Main ENDDDDDDDDDDDDDD')

#If accessed directly exit
if __name__ == '__main__':
    exit()