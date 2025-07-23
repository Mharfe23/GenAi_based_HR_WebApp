from google import genai
from google.genai import types
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()


texts = [
    "nlp",
    "natural language processing",
    "llm",
    "large language model"
    ]

result = [
    np.array(e.values) for e in client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts, 
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
]

# Calculate cosine similarity. Higher scores = greater semantic similarity.

embeddings_matrix = np.array(result)
similarity_matrix = cosine_similarity(embeddings_matrix)

print(similarity_matrix)













# from sentence_transformers import SentenceTransformer

# # Load the model
# model = SentenceTransformer("Qwen/Qwen3-Embedding-4B")

# queries = [
#     "cypress",
#     "python",
#     "testing",
#     "automated test"
# ]
# documents = [
#     "flask",
#     "AI",
#     "selenium",
    
# ]

# # Encode the queries and documents. Note that queries benefit from using a prompt
# # Here we use the prompt called "query" stored under `model.prompts`, but you can
# # also pass your own prompt via the `prompt` argument
# query_embeddings = model.encode(queries, prompt_name="query")
# document_embeddings = model.encode(documents)

# # Compute the (cosine) similarity between the query and document embeddings
# similarity = model.similarity(query_embeddings, document_embeddings)
# print(similarity)

# def filter_skills(raw_skills: set, dictionnaire: set):
#     dict_list = list(dictionnaire)
    