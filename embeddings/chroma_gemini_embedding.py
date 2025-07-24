from langchain_community.vectorstores import Chroma
import numpy as np
from langchain.schema import Document
from embeddings.google_langchain_chroma_Adapter import FixedGoogleEmbedding
from dotenv import load_dotenv


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

# ✅ This returns a retriever interface with similarity search
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.9,  # Adjust this threshold based on experimentation
        "k": 1
    }
)

def add_unique_skills(skills: list[str]):
    """Adds skills if they don't already exist."""
    documents = [Document(page_content=skill) for skill in skills]
    ids = [skill for skill in skills]
    vectorstore.add_documents(documents, ids=ids)
    print(f"✅ Added {len(skills)} skills to Chroma.")

def find_similar_skill(skill: str):
    """Finds a similar skill using LangChain's retriever abstraction."""
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
