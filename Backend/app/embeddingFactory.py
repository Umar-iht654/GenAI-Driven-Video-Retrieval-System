#script to be use as a switchboard 
#Instead of hardcoding local or OpenAI everywhere
#I can switch "local" to "openai" without rewriting the rest of the system.

#import functions from the code we made before 
from app.embeddingLocal import generate_local_embedding, generate_local_embeddings
from app.embeddingOpenAI import generate_openai_embedding, generate_openai_embeddings


# Return the correct single-text embedding function
def get_single_embedding_function(provider: str):
    if provider == "local":
        return generate_local_embedding
    elif provider == "openai":
        return generate_openai_embedding
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


# Return the correct batch embedding function
def get_batch_embedding_function(provider: str):
    if provider == "local":
        return generate_local_embeddings
    elif provider == "openai":
        return generate_openai_embeddings
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")