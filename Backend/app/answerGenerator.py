import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the .env file into the environment
# This allows us to access things like OPENAI_API_KEY securely
load_dotenv()

class OpenAIServiceError(Exception):
    pass


def get_openai_client() -> OpenAI:
    # Read the OpenAI API key from environment variables only when answer generation is needed
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise OpenAIServiceError("OPENAI_API_KEY is not configured on the backend.")

    return OpenAI(api_key=api_key)

NO_CONTEXT_ANSWER = "I could not find any relevant transcript chunks for that question."
NO_CONTEXT_SUMMARY = "No relevant transcript context was retrieved, so I could not generate a grounded summary."


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


def sanitize_plain_text(text: str) -> str:
    # Normalize line endings and trim surrounding whitespace first
    cleaned_text = text.replace("\r\n", "\n").strip()

    # Remove common markdown heading and emphasis markers if the model adds them anyway
    cleaned_text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", cleaned_text)
    cleaned_text = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned_text)
    cleaned_text = re.sub(r"__(.*?)__", r"\1", cleaned_text)

    # Strip list markers and stray asterisks that would show up literally in the UI
    cleaned_text = re.sub(r"(?m)^\s*[-*]\s+", "", cleaned_text)
    cleaned_text = cleaned_text.replace("*", "")

    # Collapse excessive blank lines without flattening the response into one paragraph
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()


def build_summary_fallback(answer: str) -> str:
    # Return a sensible fallback if the answer is empty after cleaning
    if not answer:
        return "No summary available."

    # Use the first one or two sentences to keep the summary concise for the UI
    summary_sentences = re.split(r"(?<=[.!?])\s+", answer)
    summary = " ".join(summary_sentences[:2]).strip()

    return summary or answer


def parse_model_response(raw_text: str) -> dict:
    # Clean the raw model response before looking for the expected labels
    cleaned_text = sanitize_plain_text(raw_text)

    # Extract the answer and summary sections if the model follows the requested format
    match = re.search(
        r"(?is)\b(?:answer|short direct answer):\s*(.*?)\s*\b(?:summary|brief summary):\s*(.*)",
        cleaned_text,
    )

    if match:
        answer = sanitize_plain_text(match.group(1))
        summary = sanitize_plain_text(match.group(2))
    else:
        answer = re.sub(r"(?is)^\s*(?:answer|short direct answer):\s*", "", cleaned_text)
        summary = build_summary_fallback(answer)

    # Ensure both response fields are populated for the frontend
    if not answer:
        answer = "The answer is not clearly contained in the provided transcript context."

    if not summary:
        summary = build_summary_fallback(answer)

    return {
        "answer": answer,
        "summary": summary,
    }


# Generate an answer using retrieved transcript chunks
def generate_answer(question: str, retrieved_chunks: list[dict], max_chunks: int = 5) -> dict:
    # Handle case where no chunks were retrieved
    # If FAISS or retrieval found nothing useful, return a fallback response
    if not retrieved_chunks:
        return {
            "answer": NO_CONTEXT_ANSWER,
            "summary": NO_CONTEXT_SUMMARY,
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
- Return plain text only.
- Do not use markdown.
- Do not use asterisks.
- Do not use bold formatting.
- Do not use numbered markdown headings such as Summary with emphasis markers.
- Do not use bullet points.
- Return exactly this format:
Answer: one concise plain-text answer
Summary: a brief plain-text summary in 2-4 sentences
"""

    # Send the prompt to the OpenAI Responses API
    # gpt-4.1-mini generates the grounded answer based on the transcript context
    try:
        response = get_openai_client().responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
    except OpenAIServiceError:
        raise
    except Exception as exc:
        raise OpenAIServiceError("OpenAI answer generation failed.") from exc

    # Return both:
    # 1. the generated answer text
    # 2. the chunk metadata for the chunks that were used
    parsed_response = parse_model_response(response.output_text)

    return {
        "answer": parsed_response["answer"],
        "summary": parsed_response["summary"],
        "chunks_used": format_chunk_references(selected_chunks)
    }
