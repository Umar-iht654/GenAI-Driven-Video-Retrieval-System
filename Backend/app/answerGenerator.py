import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the .env file into the environment
# This allows us to access things like OPENAI_API_KEY securely
load_dotenv()

# Read the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Stop the program if the API key was not found
# This prevents the OpenAI client from being created without authentication
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

# Create an OpenAI client using the API key
# This client will be used to send requests to the OpenAI API
client = OpenAI(api_key=api_key)


# Build transcript context from retrieved chunks
def build_context(chunks: list[dict]) -> str:
    # This list will hold formatted text for each retrieved chunk
    context_parts = []

    # Loop through each transcript chunk
    for chunk in chunks:
        # Format each chunk into a readable block of text
        # This includes metadata plus the actual transcript text
        context_parts.append(
            f"Chunk ID: {chunk['chunk_id']}\n"
            f"Video ID: {chunk['video_id']}\n"
            f"Start: {chunk['start']:.2f}\n"
            f"End: {chunk['end']:.2f}\n"
            f"Text: {chunk['text']}\n"
        )

    # Join all formatted chunk blocks together into one big context string
    # This string will be given to the model as supporting evidence
    return "\n\n".join(context_parts)


# Format chunk references for output
def format_chunk_references(chunks: list[dict]) -> list[dict]:
    # Return a simplified list of chunk metadata
    # This is useful for the frontend or API response
    # so I know which chunks were actually used
    return [
        {
            "chunk_id": chunk["chunk_id"],  # unique chunk identifier
            "video_id": chunk["video_id"],  # which video the chunk came from
            "start": chunk["start"],        # chunk start timestamp
            "end": chunk["end"]             # chunk end timestamp
        }
        for chunk in chunks
    ]


# Generate an answer using retrieved transcript chunks
def generate_answer(question: str, retrieved_chunks: list[dict], max_chunks: int = 5) -> dict:
    # Handle case where no chunks were retrieved
    # If FAISS or retrieval found nothing useful, return a fallback response
    if not retrieved_chunks:
        return {
            "answer": "I could not find any relevant transcript chunks for that question.",
            "chunks_used": []
        }

    # Limit number of chunks sent to the model
    # This prevents the prompt from getting too long or noisy
    # Usually top 3-5 chunks is enough in retrieval-based QA systems
    selected_chunks = retrieved_chunks[:max_chunks]

    # Build transcript context from the selected chunks
    # This creates the text evidence the model will use to answer
    context = build_context(selected_chunks)

    # Prompt for the model
    prompt = f"""
You are helping a student understand lecture content.

Use only the transcript context below to answer the question.
If the answer is not clearly contained in the context, say so.

Question:
{question}

Transcript Context:
{context}

Instructions:
- Give a concise and clear answer.
- Base the answer only on the provided context.
- Do not make up facts that are not present in the context.

Provide:
1. A short direct answer
2. A brief summary in 2-4 sentences
"""

    # Send the prompt to the OpenAI Responses API
    # gpt-4.1-mini generates the grounded answer based on the transcript context
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    # Return both:
    # 1. the generated answer text
    # 2. the chunk metadata for the chunks that were used
    return {
        "answer": response.output_text.strip(),
        "chunks_used": format_chunk_references(selected_chunks)
    }