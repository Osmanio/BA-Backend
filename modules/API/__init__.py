from flask import Flask, jsonify, request
app = Flask(__name__)

import main_module as main_module
from modules.MongoDB import mongodb_connect

#Initilaize the connection and store it in CONSTANTS
CONNECTION = mongodb_connect.initialize_connection()
DATABASE = CONNECTION.get('DATABASE')
CLIENT = CONNECTION.get('CLIENT')
COLLECTION = CONNECTION.get('COLLECTION')

#This is the route which takes one image url
@app.route('/SingleURL/v1/')
def hello_world():

    try:
        context = ""
        file = ""
        #url = request.args.get('url')
        #Instagram adds a few arguments to the string so we need to get the query_string instead of request.args.get('url')
        url = request.query_string.decode('utf-8').lstrip('url=')
        print(url)


        id = main_module.main(file,url)

        co = DATABASE.get_collection("db2").find(
            {"_id": id}
        )

        for x in co:
            context = x
            print(x)

        return jsonify(context), 200
    except Exception as e:
        print(e)
        return jsonify(e), 200
if __name__ == '__main__':
    app.run(debug=True)

