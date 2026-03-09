from pathlib import Path

from app.db import chunks_collection
from app.faissIndex import build_faiss_index, save_faiss_index, save_mapping


ROOT = Path(__file__).resolve().parents[2]

# Folder to store FAISS index files
INDEX_DIR = ROOT / "Data" / "faiss"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# File paths
INDEX_PATH = INDEX_DIR / "local_index.faiss"
MAPPING_PATH = INDEX_DIR / "local_mapping.json"


# Fetch chunks that have local embeddings
chunks = list(
    chunks_collection.find(
        {"local_embedding": {"$exists": True}},
        {"chunk_id": 1, "local_embedding": 1}
    )
)

if not chunks:
    raise ValueError("No chunks with local embeddings found in MongoDB.")

print(f"Found {len(chunks)} chunks with local embeddings.")


# Extract embeddings for FAISS
embeddings = []
mapping = []

for i, chunk in enumerate(chunks):
    embeddings.append(chunk["local_embedding"])

    mapping.append({
        "faiss_position": i,
        "mongo_id": str(chunk["_id"]),
        "chunk_id": chunk["chunk_id"]
    })


# Build the FAISS index
index = build_faiss_index(embeddings)

# Save FAISS index
save_faiss_index(index, INDEX_PATH)

# Save mapping file
save_mapping(mapping, MAPPING_PATH)

print(f"FAISS index saved to: {INDEX_PATH}")
print(f"Mapping file saved to: {MAPPING_PATH}")