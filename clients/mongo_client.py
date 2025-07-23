import os
import dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
from pymongo.errors import PyMongoError

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


dotenv.load_dotenv()
DB_PASSWORD = os.environ.get("MONGO_PASS")
uri_mongo = f"mongodb+srv://mharfe:{DB_PASSWORD}@clusterstage2a.ceideum.mongodb.net/?retryWrites=true&w=majority&appName=ClusterStage2A"

if not DB_PASSWORD:
    raise ValueError("MongoDB credentials are not set in environment variables.")


def _mongo_init(db_name="ResumeDB", collection_name="Candidats"):
    """Initialize MongoDB connection and return the specified collection."""
    try:
        mongo_client = MongoClient(uri_mongo, server_api=ServerApi('1'))
        db = mongo_client[db_name]
        collection = db[collection_name]
        logger.info(f"MongoDB connection established successfully for collection: {collection_name}.")
        return collection
    except PyMongoError as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

##For Singleton DB connection
collection_candidat = _mongo_init()


def mongo_candidat_init():
    return collection_candidat

################# Dictionnary (Set in this case) for skills 

##For Singleton DB connection
collection_skills = _mongo_init(collection_name="skills")

def add_new_technologies(new_tech, doc_id="tech_stack"):
    """Add new technologies to existing ones """
    collection_skills.update_one(
        {"_id":doc_id},
        {
            "$addToSet":{
                "technologies":{"$each": new_tech} 
                }
        }
    )

def replace_all_technologies(tech_list, doc_id="tech_stack"):
    """ Replace the whole technologies list"""

    collection_skills.update_one(
        {"_id": "tech_stack"},
        {"$set": {"technologies": tech_list}}
    )


def init_techs_if_not_exist(tech_list, doc_id="tech_stack"):
    """Init the first technologies list"""
    existing_doc = collection_skills.find_one({"_id": "tech_stack"})
    if not existing_doc:
        collection_skills.insert_one({
            "_id": "tech_stack",
            "technologies": tech_list
        })
        logger.info("Inserted new tech stack document.")
    else:
        logger.info("Document already exists. No insert performed.")