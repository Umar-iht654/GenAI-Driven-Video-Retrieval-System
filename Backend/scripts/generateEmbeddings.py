from app.db import chunks_collection
from app.embeddingFactory import get_single_embedding_function


# Use local embeddings for development
embedding_function = get_single_embedding_function("local")


# Find chunks that do not yet have local embeddings
chunks = list(chunks_collection.find({"local_embedding": {"$exists": False}}))

print(f"Found {len(chunks)} chunks without local embeddings.")


for chunk in chunks:
    text = chunk["text"]

    # Generate local embedding
    embedding = embedding_function(text)

    # Store embedding back in MongoDB
    chunks_collection.update_one(
        {"_id": chunk["_id"]},
        {"$set": {"local_embedding": embedding}}
    )

print("Finished generating local embeddings.")