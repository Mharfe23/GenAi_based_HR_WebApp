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
        logger.info("MongoDB connection established successfully.")
        return collection
    except PyMongoError as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

collection = _mongo_init()

def mongo_init():
    return collection