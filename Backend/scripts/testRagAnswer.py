from pathlib import Path
import numpy as np
from bson import ObjectId

from app.faissIndex import load_faiss_index, load_mapping
from app.embeddingFactory import get_single_embedding_function
from app.db import chunks_collection
from app.answerGenerator import generate_answer


# Get project root
ROOT = Path(__file__).resolve().parents[2]

# Paths to FAISS files
INDEX_PATH = ROOT / "Data" / "faiss" / "local_index.faiss"
MAPPING_PATH = ROOT / "Data" / "faiss" / "local_mapping.json"


# Load FAISS index and mapping
index = load_faiss_index(INDEX_PATH)
mapping = load_mapping(MAPPING_PATH)

# Use local embeddings for development queries
embed = get_single_embedding_function("local")


def retrieve_chunks(query: str, k: int = 3) -> list[dict]:
    # Generate embedding for the user query
    query_embedding = embed(query)

    # Convert query embedding into NumPy float32 format for FAISS
    query_vector = np.array([query_embedding], dtype="float32")

    # Search the FAISS index
    distances, indices = index.search(query_vector, k)

    retrieved_chunks = []

    # Go through returned FAISS positions
    for rank, faiss_idx in enumerate(indices[0]):
        # Skip invalid results
        if faiss_idx == -1:
            continue

        # Look up mapping info
        chunk_info = mapping[faiss_idx]

        # Convert stored MongoDB id string back to ObjectId
        mongo_id = ObjectId(chunk_info["mongo_id"])

        # Fetch full chunk from MongoDB
        chunk = chunks_collection.find_one({"_id": mongo_id})

        if chunk:
            # Add FAISS distance to the chunk for debugging / inspection
            chunk["distance"] = float(distances[0][rank])
            retrieved_chunks.append(chunk)

    return retrieved_chunks


def main():
    # Ask the user for a question
    query = input("Enter a question: ").strip()

    # Retrieve top matching transcript chunks
    retrieved_chunks = retrieve_chunks(query, k=3)

    if not retrieved_chunks:
        print("\nNo relevant chunks were found.")
        return

    # Generate final answer using retrieved chunks
    result = generate_answer(query, retrieved_chunks)

    print("\nGenerated Answer:\n")
    print(result["answer"])

    print("\nChunks Used:\n")
    for chunk in result["chunks_used"]:
        print(
            f"- {chunk['chunk_id']} "
            f"(Video: {chunk['video_id']}, "
            f"{chunk['start']:.2f}s to {chunk['end']:.2f}s)"
        )

    print("\nRetrieved Chunk Previews:\n")
    for chunk in retrieved_chunks:
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Distance: {chunk['distance']:.4f}")
        print(f"Text: {chunk['text'][:250]}")
        print("-" * 60)


if __name__ == "__main__":
    main()