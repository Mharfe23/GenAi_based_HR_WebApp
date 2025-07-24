import numpy as np
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

class FixedGoogleEmbedding(GoogleGenerativeAiEmbeddingFunction):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raw_embeddings = super().__call__(texts)
        # Convert each np.ndarray or list to a plain Python list of floats
        embeddings = []
        for emb in raw_embeddings:
            if isinstance(emb, np.ndarray):
                embeddings.append(emb.tolist())
            elif isinstance(emb, list):
                embeddings.append(emb)
            else:
                raise TypeError(f"Unexpected embedding type: {type(emb)}")
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        # GoogleGenerativeAiEmbeddingFunction.__call__ expects a list input, so wrap text in list
        raw_embedding = super().__call__([text])
        emb = raw_embedding[0]
        if isinstance(emb, np.ndarray):
            return emb.tolist()
        elif isinstance(emb, list):
            return emb
        else:
            raise TypeError(f"Unexpected embedding type: {type(emb)}")
