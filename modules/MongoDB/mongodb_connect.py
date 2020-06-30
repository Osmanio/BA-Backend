import pymongo

def initialize_connection():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["db"]
    collection = db["db2"]
    context = {
        "CLIENT": client,
        "DATABASE": db,
        "COLLECTION": collection
    }
    return context