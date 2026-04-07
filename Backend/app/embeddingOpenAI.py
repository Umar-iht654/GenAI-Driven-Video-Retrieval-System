import os
from dotenv import load_dotenv
from openai import OpenAI


# Load variables from .env
load_dotenv()


def get_openai_client() -> OpenAI:
    # Read OpenAI API key only when OpenAI embeddings are requested
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    return OpenAI(api_key=api_key)


# Generate an OpenAI embedding for a single piece of text
def generate_openai_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    response = get_openai_client().embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding


# Generate OpenAI embeddings for multiple pieces of text
def generate_openai_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    response = get_openai_client().embeddings.create(
        model=model,
        input=texts
    )
    return [item.embedding for item in response.data]
