import os
import nltk
import requests
from collections import Counter
from nltk.corpus import stopwords
import pprint
from termcolor import colored
pp = pprint.PrettyPrinter(indent=4)
from langdetect import detect
import re

from modules.MongoDB import mongodb_connect

import configparser
import sys
from pathlib import Path

#CONFIGURATION
ROOT_DIR = sys.path[1]
CONFIG_FILE = Path(ROOT_DIR) / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)


CONFIG_CLIENT = config['mongodb']['client']
CONFIG_DB = config['mongodb']['db']
CONFIG_COLLECTION = config['mongodb']['collection']

CONFIG_ITERATIONS = config['rim']['count_of_iterations']

CONFIG_BAD_WORDS_DE = config['source_files']['bad_words_de']
CONFIG_BAD_WORDS_EN = config['source_files']['bad_words_en']




#Initilaize the connection and store it in CONSTANTS
CONNECTION = mongodb_connect.initialize_connection()
DATABASE = CONNECTION.get('DATABASE')
CLIENT = CONNECTION.get('CLIENT')
COLLECTION = CONNECTION.get('COLLECTION')



def check_float(f):
    try:
        float(f)
        return True
    except ValueError:
        return False

#INITIALIZE GOOGLE API credentials to make API calls
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), 'GOOGLE.json')


#INITIALIZE stopwords
stopwords_english = set(stopwords.words('english'))
stopwords_german = set(stopwords.words('german'))


#INITIALIZE Dictionary
d = {}
d_sorted = {}
timeout = False

def get_image_attributes(url, image_url):
    # Split the image url by the extension because some webpages adding dynamically a suffix for size
    image_url = image_url.rsplit(".", 1)[0]
    #headers = {'User-Agent': 'Mozilla/5.0'}


    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    try:
        website = requests.get(url, verify=False, headers=headers, timeout=(3,5))  # Timeout if page not loading
    except requests.exceptions.Timeout as e:
        print(e)
        return ""

    print(website)

    soup = BeautifulSoup(website.content,features='html.parser')
    images = soup.findAll('img', {"src" : re.compile(r".*")})
    print('image_url :', image_url)


    for image in images:
        #print(image.attrs['src'])
        if image_url in image.attrs['src']:
            print(image.attrs)
            return image.attrs
    return ""


'''
INPUT: Website URL
OUTPUT: The content from the website
'''
#http://www.useragentstring.com/pages/useragentstring.php


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time

def get_website_content(url):
    global timeout
    timeout = False
    #headers = {'User-Agent': 'Mozilla/5.0'}
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

    #NEW METHOD
    options = Options()
    options.headless = False
    options.add_argument("--enable-javascript")
    driver = webdriver.Firefox(options=options)


    print(colored('Getting website content from URL', 'red'))
    try:
        #website = requests.get(url, headers=headers,verify=False, timeout=(3, 5))
        #driver.set_page_load_timeout(10)
        driver.get(url)
        print("Current session is {}".format(driver.session_id))
    except requests.exceptions.Timeout as e:
        print(e)
        timeout = True
        return ""

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    #soup = BeautifulSoup(website.content, features='html.parser')
    driver.quit()
    print(colored('Website content succesfully parsed', 'green'))
    return soup.get_text()


'''
INPUT: Website content
OUTPUT: Tokenized website content (lower case)
'''
def tokenize_content(content):
    print(colored('Starting to tokenize content', 'red'))
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    print(colored('Content tokenized', 'green'))
    return tokenizer.tokenize(content.lower())

    #return word_tokenize(content)


'''
INPUT: Tokenized content
OUTPUT: Filtered content 

Numbers are filtered out because without semantic analysis numbers can not be toxic.
'''
def filter_tokenized_content(content, language):

    #Remove all numbers
    content_no_numbers = [i for i in content if not i.isdigit()]
    print(content)
    if language == 'en':
        return [w for w in content_no_numbers if not w in stopwords_english]
    elif language == 'de':
        return [w for w in content_no_numbers if not w in stopwords_german]
    else:
        return content_no_numbers


'''
INPUT: Filtered content
OUTPUT: The counted filtered content
'''
def count_words(w, language):
    print(colored('Starting to count words', 'red'))

    #Return a list of the n most common elements and their counts from the most common to the least. If n is omitted or None, most_common() returns all elements in the counter. Elements with equal counts are ordered arbitrarily:
    #pp.pprint((Counter(w.title().lower() for w in w).most_common(10)))

    #list = Counter(w.title().lower() for w in w).most_common()
    list = Counter(w.title().lower() for w in w)
    pp.pprint(list)
    #a = Counter(w.title().lower() for w in w)
    #b = Counter(w.title().lower() for w in w)
    #c = a+b

    print(colored('Words counted', 'green'))



    aggregate_keywords(list, language)
    print('MEGED LIST BELOW')
    return list
    #return [Counter(w.title() for w in w)]









from modules.API.google_api_optical_character_recognition_local import main as ocrl


'''
INPUT: Image File
OUTPUT: OCR or False
'''
#Sometimes the API returns a float for empty OCR. So we handle that "Exception"
def ocr_check(ocr):
    if ocr and not check_float(ocr[0]):
        print('OCR: ', ocr)
        return ocr
    else:
        return False



'''
This method creates the aggreagtion of all ReverseImagesMetadata Keyword Set's
'''
akg = Counter() #global variable as storage
akgDE = Counter()
akgEN = Counter()
def aggregate_keywords(akl, language):
    global akg
    global akgDE
    global akgEN
    #akg = akg + akl
    if language == 'en':
        akgEN = akgEN + akl
        return akgEN.most_common()
    elif language == 'de':
        akgDE = akgDE + akl
        return akgDE.most_common()
    else:
        return ""

flagged = False #global flagged variable
# We pass num variable as OCR to detect if it's for ReverseImagesMetadata item or for OCR
def check_flag(language,tokenized_content, id, num):
    global flagged
    if language == 'en':
        return check_wordlist_en(tokenized_content, id, num)
    elif language == 'de':
        return check_wordlist_de(tokenized_content, id, num)
    else:
        return "UNKNOWN"


def check_wordlist_en(tokenized_content, id, num):
    badwords = []
    global flagged
    flag = False
    #OCR
    if num == 'OCR':
        print('OCR')
        print(tokenized_content)
        print(id)

        print('VOR BEARBEITEN')
        tokenizer = nltk.RegexpTokenizer(r"\w+")
        tokenized_content_nltk = tokenizer.tokenize(tokenized_content)
        print('TOKENIZED CONTENT FROM NLTK: ', tokenized_content_nltk)

        for x in tokenized_content_nltk:
            with open(Path(CONFIG_BAD_WORDS_EN),
                      encoding="utf-8") as f:
                contents = [x.strip() for x in f.readlines()]
                for line in contents:
                    if x.lower() == line.lower():
                        print('FLAGGED KEYWORD: ' + x.lower())
                        print(badwords)
                        badwords.append(str(x.lower()))
                        flag = True
                        flagged = True
                        print(badwords)
                        print(id)

        badwords_no_duplicates = badwords = list(dict.fromkeys(badwords))
        DATABASE.get_collection(CONFIG_COLLECTION).update_one(
            {"_id": id},
            # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
            {"$set": {
                "OCRToxicTerms": badwords_no_duplicates
            }
            }
        )
        return flag
    else:
        print('NICHT OCR')
        for x in tokenized_content:
            with open(Path(CONFIG_BAD_WORDS_EN),
                      encoding="utf-8") as f:
                contents = [x.strip() for x in f.readlines()]
                for line in contents:
                    if x.lower() == line.lower():
                        print('FLAGGED KEYWORD: ' + x.lower())
                        badwords.append(x.lower())
                        flag = True
                        flagged = True

        badwords_no_duplicates = badwords = list(dict.fromkeys(badwords))
        DATABASE.get_collection(CONFIG_COLLECTION).update_one(
            {"_id": id},
            # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
            {"$set": {
                "ReverseImagesMetadata." + str(num) + ".ToxicTerms": badwords
            }
            }
        )
    return flag

#http://www.insult.wiki/wiki/Schimpfwort-Liste#Technische_Informationen
def check_wordlist_de(tokenized_content, id, num):
    badwords = []
    global flagged
    flag = False
    # OCR
    if num == 'OCR':
        print('OCR')
        print(tokenized_content)
        print(id)
        print('VOR BEARBEITEN')
        tokenizer = nltk.RegexpTokenizer(r"\w+")
        tokenized_content_nltk = tokenizer.tokenize(tokenized_content)
        print('TOKENIZED CONTENT FROM NLTK: ', tokenized_content_nltk)
        for x in tokenized_content_nltk:
            with open(Path(CONFIG_BAD_WORDS_DE),
                      encoding="utf-8") as f:
                contents = [x.strip() for x in f.readlines()]
                for line in contents:
                    if x.lower() == line.lower():
                        print('FLAGGED KEYWORD: ' + x.lower())
                        badwords.append(str(x.lower()))
                        flag = True
                        flagged = True

        badwords_no_duplicates = badwords = list(dict.fromkeys(badwords))
        DATABASE.get_collection(CONFIG_COLLECTION).update_one(
            {"_id": id},
            # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
            {"$set": {
                "OCRToxicTerms": badwords_no_duplicates
            }
            }
        )
        return flag
    else:
        print('NICHT OCR')
        for x in tokenized_content:
            with open(Path(CONFIG_BAD_WORDS_DE),
                      encoding="utf-8") as f:
                contents = [x.strip() for x in f.readlines()]
                for line in contents:
                    if x.lower() == line.lower():
                        print('FLAGGED KEYWORD: ' + x.lower())
                        badwords.append(x.lower())
                        flag = True
                        flagged = True

        badwords_no_duplicates = badwords = list(dict.fromkeys(badwords))
        DATABASE.get_collection(CONFIG_COLLECTION).update_one(
            {"_id": id},
            # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
            {"$set": {
                "ReverseImagesMetadata." + str(num) + ".ToxicTerms": badwords
            }
            }
        )
    return flag


#Flagged is whole time false until it's getting true so no need to do anything further
def check_ocr_all_languages(content, id):
    global flagged
    print(content, flagged)
    content_as_string = ''
    for x in content:
        content_as_string += x + ' '
    #We pass num variable as OCR to detect if it's for ReverseImagesMetadata item or for OCR
    flag_en = check_wordlist_en(content_as_string, id, 'OCR')
    flag_de = check_wordlist_de(content_as_string, id, 'OCR')
    print('CHECK_OCR_ALL_LANGUAGES_DONE')

def filter_digits(input):
    filtered_list = []
    for i, word in enumerate(input):
        print(word)
        if word.isdigit():
            continue
        else:
            filtered_list += [word]
    return filtered_list

from modules.API.google_api_detect_web_entities_and_pages_local import main as dweapl
'''
INPUT: URL
OUTPUT:
    True if the URL matching the filtered urls 
    False if the URL not matching the filtered urls
'''
from tld import get_tld
def check_domain(url):
    domain_list = [
        'twitter',
        'youtube',
        '9gag',
        'facebook',
        'vimeo',
        'xing',
        'linkedin',
        'pinterest',
        'snapchat',
        'tiktok',
        'reddit',
        'pixelfed',
        'gettyimages'
    ]
    try:
        #Return the domain in lowercase
        for domain in domain_list:
            print(domain)
            if domain == get_tld(url,as_object=True,fix_protocol=True).domain:
                return True
        return False
    except Exception as e:
        print(e)
        return False

from modules.API.google_api_detect_web_entities_and_pages_remote import main as dweapr

from modules.API.google_api_optical_character_recognition_remote import main as ocrr


#This method is runned if you call this component
def main(path, url):
    global flagged
    global timeout
    print('MAIN1')
    #PATH = FILE # URL = URL


    # Here the API is used. We store the ID to continue our work with that later
    #id = dweapl(path)
    print(url)
    detect_web_entities = dweapr(url)
    id =  detect_web_entities[0]
    already_in_database = detect_web_entities[1]
    print(detect_web_entities, id, already_in_database)

    if not already_in_database:
        print('NOT IN DATABASE')
        #STEP00 - OCR
        # Here the API is used. We check for Text in the image. Input: Image Output: False, or Text
        #ocr = ocrl(path)
        ocr = ocrr(url)

        ocr = ocr_check(ocr)

        if ocr:
            check_ocr_all_languages(ocr, id)
        else:
            pass

        # We getting a cursor object which contains the database record
        # Get the cursor object -> Get the element (here 1) from the cursor object -> get the ReverseImageMetadata as array/list
        # HERE also change ImageHash, md5hash or ImageURL path/uri
        co = DATABASE.get_collection(CONFIG_COLLECTION).find(
            {"ImageHash": id}, {"ReverseImagesMetadata"}
        )
        print(id)
        rim = ""

        for x in co:
            print(x)
            print('VOR WE HAVE')
            rim = x["ReverseImagesMetadata"]

        print('We have ' + str(len(rim)) + ' records to process.')
        from datetime import date
        today = date.today()
        if str(len(rim)) == str(0):

            DATABASE.get_collection(CONFIG_COLLECTION).update_one(
                {"_id": id},
                # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
                {"$set": {"OCRText": ocr,
                          "ReverseImageMetadataNone": True,
                          "Date": str(today),
                          "Flag": flagged,
                          "ImageURL": url}}
            )
            return id
        else:
            for num, x in enumerate(rim):
                global CONFIG_ITERATIONS
                print(colored('NUM ' + str(num) + ' CONFIG_NUM: ' + str(CONFIG_ITERATIONS), 'yellow'))
                #This is to limit the steps which our application takes
                if num == int(CONFIG_ITERATIONS): break

                #If the URL is in our filtered url-list this element is skipped
                if check_domain(x['ReverseImagePageURL']):
                    #If one record is skipped we increase counter by 1 to look for another record instead
                    CONFIG_ITERATIONS = int(CONFIG_ITERATIONS)+1
                    continue


                page_url = x['ReverseImagePageURL']


                # STEP01 - Get the website content
                website_content = get_website_content(page_url)

                # STEP02 - Tokenize the website content
                tokenized_content = tokenize_content(website_content)
                print(tokenized_content)

                print(website_content)

                if website_content == "":
                    language = "UNKNOWN"
                else:
                    language = detect(website_content)

                # STEP03 - Filter tokenized content by stopwords
                filtered_tokenized_content = filter_tokenized_content(tokenized_content, language)

                # STEP04 - Count keywords
                counted_keywords = count_words(filtered_tokenized_content,language)

                print('TRENNER')
                print(tokenized_content)
                print('TRENNER')





                page_url_record = COLLECTION.find_one(
                    {"_id": id}
                )

                page_url_html = page_url_record['ReverseImagesMetadata'][num]['ReverseImagePageURL']
                image_url_html = page_url_record['ReverseImagesMetadata'][num]['ReverseImageURL']
                print('Begin of Image Attribute Getter')
                print(page_url_html, image_url_html)


                DATABASE.get_collection(CONFIG_COLLECTION).update_one(
                    {"_id": id},
                    # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
                    {"$set": {"ReverseImagesMetadata." + str(num) + ".Keywords": str(filtered_tokenized_content),
                              "ReverseImagesMetadata." + str(num) + ".KeywordsAggregated": counted_keywords,
                              "ReverseImagesMetadata." + str(num) + ".Language": language,
                              "ReverseImagesMetadata." + str(num) + ".Flag": check_flag(language, tokenized_content, id, num),
                              "ReverseImagesMetadata." + str(num) + ".Date": str(today),
                              "ReverseImagesMetadata." + str(num) + ".Timeout": timeout,
                              "ReverseImagesMetadata." + str(num) + ".ReverseImageAttribute": get_image_attributes(page_url_html,image_url_html),
                              "OCRText": ocr,
                              "ReverseImagesMetadataNone": False,
                              "Flag": flagged,
                              "Date": str(today),
                              "ImageURL": url}}
                )

            # After the for loop aggregate keywords
            global akg
            global akgDE
            global akgEN
            print(akg)
            DATABASE.get_collection(CONFIG_COLLECTION).update_one(
                {"_id": id},
                # STRING OR ARRAY WHAT IS NEEDED? ARRAY WITHOUT STR() THEN
                {"$set": {"KeywordsAggregatedDE": akgDE,
                          "KeywordsAggregatedEN": akgEN,
                          "KeywordsMostCommonDE": akgDE.most_common(10),
                          "KeywordsMostCommonEN": akgEN.most_common(10)
                          }
                 }
            )
            # get_image_attributes(url, image_url)
            print('ENDE MAIN')

            #akg needs to be resettet for next image
            akg = ''
            akg = Counter()
            #akgDE = ''
            #akgDE = Counter()
            #akgEN = ''
            #akgEN = Counter()
            flagged = False
            return id



            #HERE IS EXTI REMOVE
            #return id
            #exit()
    else:
        print('ALREADY IN DATABASE')
        # akg needs to be resettet for next image
        akg = ''
        akg = Counter()
        # akgDE = ''
        # akgDE = Counter()
        # akgEN = ''
        # akgEN = Counter()
        flagged = False
        return id

#If accessed directly exit
if __name__ == '__main__':
    #main(image_file)
    main(image_url)
    #exit()

