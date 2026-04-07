from __future__ import annotations

from bson import ObjectId
from pymongo.errors import PyMongoError

from app.db import chunks_collection
from app.index_manager import IndexManager


class SearchIndexError(Exception):
    pass


class DatabaseError(Exception):
    pass


def retrieve_chunks(
    query: str,
    *,
    index_manager: IndexManager,
    embed_function,
    top_k: int = 3,
) -> list[dict]:
    if not index_manager.is_ready():
        raise SearchIndexError(
            "The search index is not ready yet. Ingest a video first or wait for indexing to finish."
        )

    # Generate an embedding vector for the user's query
    query_embedding = embed_function(query)

    try:
        search_hits = index_manager.search(query_embedding, top_k)
    except Exception as exc:
        raise SearchIndexError("The search index could not be queried.") from exc

    retrieved_chunks = []

    for chunk_info in search_hits:
        mongo_id = ObjectId(chunk_info["mongo_id"])

        try:
            chunk = chunks_collection.find_one({"_id": mongo_id})
        except PyMongoError as exc:
            raise DatabaseError("MongoDB query failed while retrieving transcript chunks.") from exc

        if chunk:
            chunk["score"] = chunk_info.get("score")
            chunk["distance"] = chunk_info["distance"]
            chunk["_id"] = str(chunk["_id"])
            retrieved_chunks.append(chunk)

    if search_hits and not retrieved_chunks:
        raise SearchIndexError(
            "The search index returned results that could not be matched to transcript chunks."
        )

    return retrieved_chunks
