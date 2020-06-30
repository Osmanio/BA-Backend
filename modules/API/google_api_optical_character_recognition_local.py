def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')

    #We just need the first element, because it contains every single keyword splitted by \n
    #If there is no text it will return None
    for text in texts:
        print(text.description)
        #We replace the /n with an empty space to split it by the empty space and convert it to a list which we will return
        return text.description.replace('\n',' ').split()

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

def main(path):
    print('Main START')
    return detect_text(path)
    print('Main END')

#If accessed directly exit
if __name__ == '__main__':
    exit()