from app.db import chunks_collection
from app.embeddingFactory import get_single_embedding_function


# Use OpenAI embeddings for evaluation
embedding_function = get_single_embedding_function("openai")


# Find chunks that do not yet have OpenAI embeddings
chunks = list(chunks_collection.find({"openai_embedding": {"$exists": False}}))

print(f"Found {len(chunks)} chunks without OpenAI embeddings.")


for chunk in chunks:
    text = chunk["text"]

    # Generate OpenAI embedding
    embedding = embedding_function(text)

    # Store embedding back in MongoDB
    chunks_collection.update_one(
        {"_id": chunk["_id"]},
        {"$set": {"openai_embedding": embedding}}
    )

print("Finished generating OpenAI embeddings.")