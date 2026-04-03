from pathlib import Path
import numpy as np
from bson import ObjectId
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.faissIndex import load_faiss_index, load_mapping
from app.embeddingFactory import get_single_embedding_function
from app.db import chunks_collection
from app.answerGenerator import generate_answer
from app.db import db  

# Create the FastAPI application instance with a title for documentation
app = FastAPI(title="AI Video Retrieval API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the root directory of the project dynamically based on this file location
ROOT = Path(__file__).resolve().parents[2]

# Define the path to the saved FAISS index file
INDEX_PATH = ROOT / "Data" / "faiss" / "local_index.faiss"

# Define the path to the FAISS mapping file linking vectors to MongoDB chunks
MAPPING_PATH = ROOT / "Data" / "faiss" / "local_mapping.json"

# Load the FAISS index once when the server starts to avoid reloading per request
index = load_faiss_index(INDEX_PATH)

# Load the mapping file once to map FAISS results back to chunk metadata
mapping = load_mapping(MAPPING_PATH)

# Load the local embedding function once so it can be reused for all queries
embed = get_single_embedding_function("local")

# Define the structure of incoming POST request data using Pydantic
class AskRequest(BaseModel):
    # The user's question to be answered by the system
    question: str
    
    # Number of top chunks to retrieve from FAISS (default is 3)
    top_k: int = 3

# Define a simple health check endpoint to verify the server is running
@app.get("/health")
def health_check():
    # Return a basic status response
    return {"status": "ok"}

# Function to retrieve relevant chunks using FAISS and MongoDB
def retrieve_chunks(query: str, k: int = 3) -> list[dict]:
    # Generate an embedding vector for the user's query
    query_embedding = embed(query)

    # Convert the embedding into a NumPy float32 array required by FAISS
    query_vector = np.array([query_embedding], dtype="float32")

    # Perform similarity search in FAISS to get nearest vectors
    distances, indices = index.search(query_vector, k)

    # Store retrieved chunks
    retrieved_chunks = []

    # Loop through returned FAISS indices and distances
    for rank, faiss_idx in enumerate(indices[0]):
        # Skip invalid indices returned by FAISS
        if faiss_idx == -1:
            continue

        # Get mapping info for this FAISS result
        chunk_info = mapping[faiss_idx]

        # Convert stored string ID back into MongoDB ObjectId
        mongo_id = ObjectId(chunk_info["mongo_id"])

        # Fetch the corresponding chunk document from MongoDB
        chunk = chunks_collection.find_one({"_id": mongo_id})

        # If chunk exists, enrich it with distance and prepare for response
        if chunk:
            # Add similarity distance for debugging or ranking insight
            chunk["distance"] = float(distances[0][rank])

            # Convert MongoDB ObjectId to string so it can be returned in JSON
            chunk["_id"] = str(chunk["_id"])

            # Add the chunk to the results list
            retrieved_chunks.append(chunk)

    # Return the list of retrieved chunks
    return retrieved_chunks

# Define the main API endpoint for asking questions
@app.post("/ask")
def ask_question(request: AskRequest):
    # Retrieve relevant chunks using semantic search
    retrieved_chunks = retrieve_chunks(request.question, request.top_k)

    # Generate an answer using the retrieved chunks and OpenAI
    result = generate_answer(request.question, retrieved_chunks)

    # Return structured JSON response to the client
    return {
        # Echo the original question
        "question": request.question,

        # Return the generated answer text
        "answer": result["answer"],

        # Return metadata about which chunks were used for the answer
        "chunks_used": result["chunks_used"],

        # Return preview information about retrieved chunks for debugging/UI display
        "retrieved_chunks": [
            {
                # Unique chunk identifier
                "chunk_id": chunk["chunk_id"],

                # Source video identifier
                "video_id": chunk["video_id"],

                # Start timestamp of the chunk
                "start": chunk["start"],

                # End timestamp of the chunk
                "end": chunk["end"],

                # Distance score from FAISS (lower = more similar)
                "distance": chunk["distance"],

                # Short preview of the transcript text
                "text_preview": chunk["text"][:300]
            }
            for chunk in retrieved_chunks
        ]
    }

@app.get("/db-test")
def db_test():
    return {"collections": db.list_collection_names()}
