import os
import dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB Setup

dotenv.load_dotenv()
DB_PASSWORD = os.environ.get("MONGO_PASS")
uri_mongo = f"mongodb+srv://mharfe:{DB_PASSWORD}@clusterstage2a.ceideum.mongodb.net/?retryWrites=true&w=majority&appName=ClusterStage2A"

def mongo_init():
    mongo_client = MongoClient(uri_mongo, server_api=ServerApi('1'))
    db = mongo_client["ResumeDB"]
    collection = db["Candidats"]
    return collection

