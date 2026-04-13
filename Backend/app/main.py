from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.answerGenerator import OpenAIServiceError, generate_answer
from app.auto_ingest import (
    ingest_existing_videos,
    start_video_watcher,
    stop_video_watcher,
)
from app.db import db
from app.embeddingFactory import get_single_embedding_function
from app.index_manager import IndexManager
from app.search_service import DatabaseError, SearchIndexError, retrieve_chunks

# Get the root directory of the project dynamically based on this file location
ROOT = Path(__file__).resolve().parents[2]

# Define the path to the saved FAISS index file
INDEX_PATH = ROOT / "Data" / "faiss" / "local_index.faiss"

# Define the path to the FAISS mapping file linking vectors to MongoDB chunks
MAPPING_PATH = ROOT / "Data" / "faiss" / "local_mapping.json"
# Define the path for the videos
VIDEO_PATH = ROOT / "Data" / "videos"
VIDEO_PATH.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    index_manager = IndexManager(INDEX_PATH, MAPPING_PATH)
    app.state.index_manager = index_manager

    # Process any videos already in the folder before loading searchable state
    ingest_existing_videos()
    index_manager.load()

    # Start watching the videos folder for newly added lecture files
    observer = start_video_watcher(reload_search_state=index_manager.reload)
    app.state.video_observer = observer

    try:
        yield
    finally:
        # Stop the watcher cleanly when the backend shuts down
        stop_video_watcher(observer)


app = FastAPI(
    title="AI Video Retrieval API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the local embedding function once so it can be reused for all queries
embed = get_single_embedding_function("local")
app.mount("/videos", StaticFiles(directory=VIDEO_PATH), name="videos")

def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
):
    content = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return build_error_response(
        status_code=422,
        code="invalid_request",
        message="The request payload is invalid.",
        details=exc.errors(),
    )


@app.exception_handler(SearchIndexError)
async def search_index_exception_handler(request: Request, exc: SearchIndexError):
    return build_error_response(
        status_code=503,
        code="index_unavailable",
        message=str(exc),
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    return build_error_response(
        status_code=503,
        code="database_error",
        message=str(exc),
    )


@app.exception_handler(OpenAIServiceError)
async def openai_exception_handler(request: Request, exc: OpenAIServiceError):
    return build_error_response(
        status_code=502,
        code="openai_error",
        message=str(exc),
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    return build_error_response(
        status_code=500,
        code="internal_server_error",
        message="An unexpected backend error occurred.",
    )

# Define the structure of incoming POST request data using Pydantic
class AskRequest(BaseModel):
    # The user's question to be answered by the system
    question: str = Field(..., min_length=1, max_length=5000)
    
    # Number of top chunks to retrieve from FAISS (default is 3)
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Question must not be empty.")

        return normalized_value


class AskResponse(BaseModel):
    # Echo the original question
    question: str

    # Main plain-text answer returned by the model
    answer: str

    # Short plain-text summary returned separately for the frontend
    summary: str

    # Metadata for the chunks that grounded the answer
    chunks_used: list[dict]

    # Retrieved chunk previews returned for UI display and debugging
    retrieved_chunks: list[dict]

# Define a simple health check endpoint to verify the server is running
@app.get("/health")
def health_check():
    # Return a basic status response
    return {"status": "ok"}

# Define the main API endpoint for asking questions
@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, http_request: Request):
    # Retrieve relevant chunks using semantic search
    retrieved_chunks = retrieve_chunks(
        request.question,
        index_manager=http_request.app.state.index_manager,
        embed_function=embed,
        top_k=request.top_k,
    )

    if not retrieved_chunks:
        return {
            "question": request.question,
            "answer": "I could not find a relevant lecture segment for that question.",
            "summary": "The indexed lecture content does not appear to contain a strong enough match.",
            "chunks_used": [],
            "retrieved_chunks": [],
        }

    # Generate an answer using the retrieved chunks and OpenAI
    result = generate_answer(request.question, retrieved_chunks)

    # Return structured JSON response to the client
    return {
        # Echo the original question
        "question": request.question,

        # Return the generated answer text
        "answer": result["answer"],

        # Return the generated summary text separately for the frontend
        "summary": result["summary"],

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

                # Cosine similarity score after normalized vector search
                "score": chunk.get("score"),

                # Distance-style value derived from cosine similarity (lower = more similar)
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
