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
MONGO_ENDPOINT = os.environ.get("MONGO_ENDPOINT")

if not MONGO_ENDPOINT:
    raise ValueError("MongoDB credentials are not set in environment variables.")


def _mongo_candidat_init(db_name="ResumeDB", collection_name="Candidats"):
    """Initialize MongoDB connection and return the specified collection."""
    try:
        mongo_client = MongoClient(MONGO_ENDPOINT, server_api=ServerApi('1'))
        db = mongo_client[db_name]
        collection = db[collection_name]
        logger.info(f"MongoDB connection established successfully for collection: {collection_name}.")
        return collection
    except PyMongoError as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

##For Singleton DB connection
collection_candidat = _mongo_candidat_init()


def mongo_candidat_init():
    return collection_candidat


def check_mongo_duplicate(email="", full_name=""):
    if email is None and full_name is None:
        return False
    query = {
        "$or": [
            {"email": email},
            {"full_name": full_name}
        ]
    }
    result = collection_candidat.find_one(query)
    return result is not None

################# Dictionnary (Set in this case) for skills 

##For Singleton DB connection

collection_skills = _mongo_candidat_init(collection_name="skills")

def add_new_skills_mongo(new_tech, doc_id="tech_stack"):
    """Add new technologies to existing ones """
    collection_skills.update_one(
        {"_id":doc_id},
        {
            "$addToSet":{
                "technologies":{"$each": new_tech} 
                }
        }
    )
    logger.info(f"Added {new_tech} to mongo skills")

def replace_all_technologies(tech_list, doc_id="tech_stack"):
    """ Replace the whole technologies list"""

    collection_skills.update_one(
        {"_id": "tech_stack"},
        {"$set": {"technologies": tech_list}}
    )


def init_techs_if_not_exist_mongo(tech_list, doc_id="tech_stack"):
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

def get_skills_mongo():
    result = dict(collection_skills.find_one())
    return list(result["technologies"])

def remove_skills_mongo(tech_list: list[str], doc_id="tech_stack"):
    for tech_name in tech_list:
        result = collection_skills.update_one(
            {"_id": doc_id},
            {"$pull": {"technologies": tech_name.lower()}}
        )
        if result.modified_count > 0:
            logger.info(f"Removed '{tech_name.lower()}' from technologies.")
        else:
            logger.info(f"'{tech_name.lower()}' not found in technologies (mongodb).")


def main():
    initial_techs = ["Python", "JavaScript", "React"]

    # 1. Initialisation si le document n'existe pas
    init_techs_if_not_exist_mongo(initial_techs)

    # 2. Ajouter de nouvelles technologies (certaines nouvelles, certaines déjà présentes)
    new_techs = ["Node.js", "Python", "Docker"]
    add_new_skills_mongo(new_techs)

    # 3. Afficher l’état actuel du document
    print("\n--- After Adding New Technologies ---")
    for doc in get_skills_mongo():
        print(doc)

    # 4. Remplacer toutes les technologies (écrase la liste précédente)
    replacement_techs = ["Go", "Rust", "Kubernetes"]
    replace_all_technologies(replacement_techs)

    # 5. Afficher l’état final
    print("\n--- After Replacing Technologies ---")
    for doc in get_skills_mongo():
        print(doc)

#if __name__ == "__main__":
    #main()
    #print(check_mongo_duplicate(full_name="Kanoja Kumar Mishr"))