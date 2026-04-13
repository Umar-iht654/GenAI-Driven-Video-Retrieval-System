# Enable forward references for type hints (useful for newer Python typing features)
from __future__ import annotations

# Import ObjectId so we can convert string IDs back into MongoDB IDs
from bson import ObjectId

# Import MongoDB-specific error handling
from pymongo.errors import PyMongoError

# Import the MongoDB collection that stores transcript chunks
from app.db import chunks_collection

# Import the FAISS index manager which handles vector search
from app.index_manager import IndexManager

# Import reranking logic to improve retrieval quality
from app.reranker import rerank_chunks

# Import relevance checks to reject weak or unrelated matches
from app.relevance import has_reasonable_keyword_overlap, is_strong_match


# Custom exception for index-related failures
class SearchIndexError(Exception):
    pass


# Custom exception for database-related failures
class DatabaseError(Exception):
    pass


# Main retrieval function that performs semantic search + reranking + filtering
def retrieve_chunks(
    query: str,
    *,
    index_manager: IndexManager,
    embed_function,
    top_k: int = 3,
) -> list[dict]:

    # Check that the FAISS index is ready before attempting search
    if not index_manager.is_ready():
        raise SearchIndexError(
            "The search index is not ready yet. Ingest a video first or wait for indexing to finish."
        )

    # Generate a vector embedding for the user's query using the embedding model
    query_embedding = embed_function(query)

    # Increase candidate pool size so we can rerank more options before selecting final results
    candidate_k = max(top_k, 8)

    try:
        # Perform FAISS search to retrieve the nearest vector matches
        search_hits = index_manager.search(query_embedding, candidate_k)
    except Exception as exc:
        # Wrap any search failure in a consistent error type
        raise SearchIndexError("The search index could not be queried.") from exc

    # Store the MongoDB chunks that correspond to FAISS results
    retrieved_chunks = []

    # Loop through each FAISS result and fetch the actual chunk from MongoDB
    for chunk_info in search_hits:
        # Convert stored string ID back into a MongoDB ObjectId
        mongo_id = ObjectId(chunk_info["mongo_id"])

        try:
            # Fetch the chunk document from MongoDB
            chunk = chunks_collection.find_one({"_id": mongo_id})
        except PyMongoError as exc:
            # Raise a clear error if MongoDB fails
            raise DatabaseError(
                "MongoDB query failed while retrieving transcript chunks."
            ) from exc

        # Only include valid chunks that were successfully retrieved
        if chunk:
            # Attach similarity score (higher = better if using cosine similarity)
            chunk["score"] = chunk_info.get("score")

            # Keep original FAISS distance for debugging or fallback logic
            chunk["distance"] = chunk_info["distance"]

            # Convert MongoDB ObjectId to string so it can be returned as JSON
            chunk["_id"] = str(chunk["_id"])

            # Add the chunk to our candidate list
            retrieved_chunks.append(chunk)

    # If FAISS returned hits but none could be matched in MongoDB, something is inconsistent
    if search_hits and not retrieved_chunks:
        raise SearchIndexError(
            "The search index returned results that could not be matched to transcript chunks."
        )

    # If no chunks were retrieved at all, return empty list early
    if not retrieved_chunks:
        return []

    # Apply heuristic reranking to improve relevance ordering
    reranked_chunks = rerank_chunks(query, retrieved_chunks)

    # Take the top reranked result as the best candidate
    best_chunk = reranked_chunks[0]

    # Reject the result if the score is too weak (prevents unrelated answers)
    if not is_strong_match(best_chunk):
        return []

    # Reject the result if there is no meaningful keyword overlap with the query
    if not has_reasonable_keyword_overlap(query, best_chunk.get("text", "")):
        return []
    
    # Reject the result if the top semantic score itself is too weak
    if float(best_chunk.get("score", 0.0)) < 0.35:
        return []

    # Return only the top_k chunks after reranking and filtering
    return reranked_chunks[:top_k]