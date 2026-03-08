from sentence_transformers import SentenceTransformer


# Load the local sentence-transformer model once
# This model will be reused every time we generate local embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")


# Generate a local embedding for a single piece of text
def generate_local_embedding(text: str) -> list[float]:
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


# Generate local embeddings for multiple pieces of text
def generate_local_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(texts, convert_to_numpy=True)
    return [embedding.tolist() for embedding in embeddings]