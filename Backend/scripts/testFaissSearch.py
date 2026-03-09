from pathlib import Path
import numpy as np
from bson import ObjectId

from app.faissIndex import load_faiss_index, load_mapping
from app.embeddingFactory import get_single_embedding_function
from app.db import chunks_collection


# Get project root
ROOT = Path(__file__).resolve().parents[2]

# Paths to FAISS files
INDEX_PATH = ROOT / "Data" / "faiss" / "local_index.faiss"
MAPPING_PATH = ROOT / "Data" / "faiss" / "local_mapping.json"

# Load FAISS index and mapping
index = load_faiss_index(INDEX_PATH)
mapping = load_mapping(MAPPING_PATH)

# Use local embeddings for development search
embed = get_single_embedding_function("local")

# Ask the user for a query
query = input("Enter a search query: ").strip()

# Generate embedding for the query
query_embedding = embed(query)

# Convert query embedding into NumPy float32 array for FAISS
query_vector = np.array([query_embedding], dtype="float32")

# Number of results to return
k = 5

# Search the FAISS index
distances, indices = index.search(query_vector, k)

print("\nTop results:\n")

for rank, faiss_idx in enumerate(indices[0]):
    # Skip invalid indices just in case
    if faiss_idx == -1:
        continue

    # Get mapping info for this FAISS result
    chunk_info = mapping[faiss_idx]

    # Convert stored MongoDB id string back into ObjectId
    mongo_id = ObjectId(chunk_info["mongo_id"])

    # Fetch the full chunk document from MongoDB
    chunk = chunks_collection.find_one({"_id": mongo_id})

    if not chunk:
        print(f"Result {rank + 1}: Chunk not found in MongoDB")
        print("-" * 60)
        continue

    print(f"Result {rank + 1}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Video ID: {chunk['video_id']}")
    print(f"Start: {chunk['start']:.2f} | End: {chunk['end']:.2f}")
    print(f"Distance: {distances[0][rank]:.4f}")
    print("Text preview:")
    print(chunk["text"][:300])
    print("-" * 60)