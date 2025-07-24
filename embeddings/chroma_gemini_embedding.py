from langchain_community.vectorstores import Chroma
from google_langchain_chroma_Adapter import FixedGoogleEmbedding
from dotenv import load_dotenv
from chromadb.errors import IDAlreadyExistsError
import logging

logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Load env variables (must include GOOGLE_API_KEY)
load_dotenv()
db_location = "./chroma_db"

# Initialize the Custom LangChain-compatible embedding function

fixed_embeding = FixedGoogleEmbedding()

# Initialize LangChain's Chroma vector store (persistent)
vectorstore = Chroma(
    collection_name="skills",
    embedding_function=fixed_embeding,
    persist_directory=db_location
)

# This returns a retriever with similarity search
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.9,
        "k": 1
    }
)

def add_unique_skills(skills: list[str]):
    """Adds skills if they don't already exist."""
    
    ids = [skill for skill in skills]
    for id in ids:
        if vectorstore.get(ids):
            logger.warning(f"⚠️ Document with id {id} already exists.")
        else:
            vectorstore.add_texts(skills, ids=id)
            logger.info(f"Added {id} skill to chroma")


def find_similar_skill(skill: str):
    """Finds a similar skill."""
    results = retriever.invoke(skill)
    if results:
        return results[0]
    return None


def main():
    skills = ["python", "java", "springboot"]
    add_unique_skills(skills)

    query = "jee"
    similar = find_similar_skill(query)

    if similar:
        print(f"🔍 Found similar skill for '{query}': {similar} ")
    else:
        print(f"❌ No similar skill found for '{query}'")

    result = vectorstore.get()
    print("adeed documents "+str(result))

if __name__ == "__main__":
    main()
    # result = vectorstore.get()
    # print("adeed documents "+str(result))