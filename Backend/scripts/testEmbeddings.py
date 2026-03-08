from app.embeddingFactory import get_single_embedding_function


sample_text = "Supervised learning uses labelled data to train a model."


# Test local embeddings
local_embedding_function = get_single_embedding_function("local")
local_embedding = local_embedding_function(sample_text)

print("LOCAL EMBEDDING")
print(f"Length: {len(local_embedding)}")
print(f"First 10 values: {local_embedding[:10]}")
print()


# Test OpenAI embeddings
openai_embedding_function = get_single_embedding_function("openai")
openai_embedding = openai_embedding_function(sample_text)

print("OPENAI EMBEDDING")
print(f"Length: {len(openai_embedding)}")
print(f"First 10 values: {openai_embedding[:10]}")