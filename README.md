# Companion Backend
Run the following command in the terminal to copy to project.

Frontend:
```
git clone git@github.com:Osmanio/BA-Frontend.git
```
Backend:
```
git clone git@github.com:Osmanio/BA-Backend.git
```

##Before you start
- Install Python 3.7 (minimum required version)
- You need to connect to the database before you start the application
- You need Desktop development with C++ installed. Get it here: https://docs.microsoft.com/de-de/cpp/build/vscpp-step-0-installation?view=vs-2019

### Create a Google developer account
Create a Google developer account to make API-Calls
1) Visit: https://cloud.google.com/vision/docs/quickstart-client-libraries
2) In the Cloud Console, on the project selector page, select or create a Cloud project
3) Make sure that billing is enabled for your Google Cloud project
4) Enable the Vision API
5) Set up authentication: \
5.1)In the Cloud Console, go to the Create service account key page \
5.2) From the Service account list, select New service account \
5.3) In the Service account name field, enter a name \
5.4) From the Role list, select Project > Owner \
5.5) Click Create. A JSON file that contains your key downloads to your computer \
5.6) This created JSON file you need to place into the root directory of the project and name it "GOOGLE.JSON"

###Create a virtual environment and install requirements
1) run the command `python -m venv venv` to create a virtual env.
2) run the virtual env. with `venv\Scripts\activate`
3) install requirements.txt
4) In this case we use pip to manage our packages so we run `pip3 install -r requirements.txt`.
If you are using something other than pip please adjust this command line.
##How to start the application?
You need to run `modules.API.__init__.py`


###Known issues
If you get the error module google.cloud not found please run this command in the terminal: 
`pip3 install google-cloud --upgrade google-cloud-vision`


If you get a SSL-Error (specially a problem on MacOS) just install certifi through this link: https://pypi.org/project/certifi/ or fix your environment. This is a locale issue with the SSL-Certificate.

If the stopwords are missing you can run a file with following 2 lines  \
`import nltk` \
`nltk.download('stopwords')` \
After that a gui will show up where you can select the languages. Here the languages are German and English.


