from langchain_community.vectorstores import Chroma
from embeddings.google_langchain_chroma_Adapter import FixedGoogleEmbedding
from dotenv import load_dotenv
import logging

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

def add_unique_skills_to_chroma(skills: list[str]):
    """Adds skills if they don't already exist."""
    
    
    for skill in skills:
        result = vectorstore.get(skill)
        if result["ids"] != []:
            logger.info(f"⚠️ Document with id {skill} already exists in chroma.")
        else:
            vectorstore.add_texts([skill],ids=[skill])
            logger.info(f"Added {skill} skill to chroma")


def find_similar_skill(skill: str):
    """Finds a similar skill."""
    results = retriever.invoke(skill)
    if results:
        return results[0].page_content
    logger.info(f"Didnt find similar for {skill}")
    return None

def remove_skills_chroma(ids):
    ids = [id.strip().lower() for id in ids]
    vectorstore.delete(ids)
    logger.info(f"deleted the following skills: {ids}")



def main():
    # skills = ["gcp","owasp"]
    # add_unique_skills_to_chroma(skills)

    query = "Ai"
    similar = find_similar_skill(query)

    if similar:
        print(f"🔍 Found similar skill for '{query}': {similar} ")
    else:
        print(f"❌ No similar skill found for '{query}'")


if __name__ == "__main__":
    main()
    # result = vectorstore.get()
    # print("adeed documents "+str(result))