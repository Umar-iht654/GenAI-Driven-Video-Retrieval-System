from pathlib import Path

# Import the MongoDB collection that stores transcript chunks
# Each chunk contains text + embedding
from app.db import chunks_collection

# Import functions we previously created for FAISS indexing
from app.faissIndex import build_faiss_index, save_faiss_index, save_mapping


# ROOT points to the root directory of the project
# __file__ = current file path
# parents[2] = go up two directories
ROOT = Path(__file__).resolve().parents[2]


# Create a folder where FAISS index files will be stored
INDEX_DIR = ROOT / "Data" / "faiss"

# mkdir creates the directory if it does not exist
# parents=True allows creation of nested folders
# exist_ok=True prevents errors if folder already exists
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# Define where the FAISS index file will be saved
INDEX_PATH = INDEX_DIR / "local_index.faiss"

# Define where the mapping JSON file will be saved
MAPPING_PATH = INDEX_DIR / "local_mapping.json"


# Fetch chunks from MongoDB that have embeddings
# We only want chunks that already have "local_embedding"
chunks = list(
    chunks_collection.find(
        {"local_embedding": {"$exists": True}},  # filter condition
        {"chunk_id": 1, "local_embedding": 1}    # fields to return
    )
)


# If no embeddings are found, stop the program
# This prevents building an empty FAISS index
if not chunks:
    raise ValueError("No chunks with local embeddings found in MongoDB.")


# Print how many chunks were found
print(f"Found {len(chunks)} chunks with local embeddings.")


# Lists to store data for FAISS
embeddings = []   # actual vectors
mapping = []      # metadata mapping


# Loop through all chunks retrieved from MongoDB
for i, chunk in enumerate(chunks):

    # Add the embedding vector to the embeddings list
    embeddings.append(chunk["local_embedding"])

    # Create a mapping entry
    # This connects FAISS index positions to MongoDB chunks
    mapping.append({
        "faiss_position": i,          # index position in FAISS
        "mongo_id": str(chunk["_id"]),# MongoDB document ID
        "chunk_id": chunk["chunk_id"] # ID used for the chunk
    })


# Build the FAISS index from all embedding vectors
index = build_faiss_index(embeddings)


# Save the FAISS index to disk
# This stores the vector database as a binary file
save_faiss_index(index, INDEX_PATH)


# Save the mapping file as JSON
# This links FAISS vector positions to MongoDB documents
save_mapping(mapping, MAPPING_PATH)


# Print confirmation messages
print(f"FAISS index saved to: {INDEX_PATH}")
print(f"Mapping file saved to: {MAPPING_PATH}")
