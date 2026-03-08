from sentence_transformers import SentenceTransformer


# Load the MiniLM embedding model
# This converts text into a dense vector representation
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text: str):
    
    # Encode text into a numerical vector
    # convert_to_numpy ensures compatibility with FAISS
    embedding = model.encode(text, convert_to_numpy=True)

    return embedding