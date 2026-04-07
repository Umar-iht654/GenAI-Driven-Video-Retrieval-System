from __future__ import annotations

from pathlib import Path

from app.auto_ingest import FAISS_INDEX_PATH, FAISS_MAPPING_PATH, rebuild_faiss_index
from app.chunker import chunk_segments
from app.db import chunks_collection
from app.embeddingFactory import (
    get_batch_embedding_function,
    get_single_embedding_function,
)
from app.index_manager import IndexManager
from app.search_service import retrieve_chunks
from app.vttParser import parse_vtt_file


ROOT = Path(__file__).resolve().parents[2]
SUBTITLES_DIR = ROOT / "Data" / "subtitles"


def resolve_subtitle_input(
    *,
    video_id: str | None = None,
    subtitle_path: str | Path | None = None,
) -> tuple[Path, str]:
    if subtitle_path is not None:
        candidate_path = Path(subtitle_path)
        if not candidate_path.is_absolute():
            candidate_path = ROOT / candidate_path

        subtitle_file = candidate_path.resolve(strict=False)
        if not subtitle_file.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")

        return subtitle_file, (video_id or subtitle_file.stem)

    if video_id is not None:
        subtitle_file = SUBTITLES_DIR / f"{video_id}.vtt"
        if not subtitle_file.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")

        return subtitle_file, video_id

    subtitle_files = sorted(SUBTITLES_DIR.glob("*.vtt"))

    if not subtitle_files:
        raise FileNotFoundError("No subtitle files were found in Data/subtitles.")

    if len(subtitle_files) > 1:
        raise ValueError(
            "Multiple subtitle files were found. Provide --video-id or --subtitle-path."
        )

    subtitle_file = subtitle_files[0]
    return subtitle_file, subtitle_file.stem


def parse_subtitle(
    *,
    video_id: str | None = None,
    subtitle_path: str | Path | None = None,
) -> dict:
    resolved_subtitle_path, resolved_video_id = resolve_subtitle_input(
        video_id=video_id,
        subtitle_path=subtitle_path,
    )
    segments = parse_vtt_file(resolved_subtitle_path)

    return {
        "subtitle_path": resolved_subtitle_path,
        "video_id": resolved_video_id,
        "segments": segments,
    }


def chunk_subtitle(
    *,
    video_id: str | None = None,
    subtitle_path: str | Path | None = None,
    max_duration: float = 60.0,
    max_words: int = 150,
) -> dict:
    parse_result = parse_subtitle(
        video_id=video_id,
        subtitle_path=subtitle_path,
    )
    chunks = chunk_segments(
        parse_result["segments"],
        video_id=parse_result["video_id"],
        max_duration=max_duration,
        max_words=max_words,
    )

    return {
        "subtitle_path": parse_result["subtitle_path"],
        "video_id": parse_result["video_id"],
        "segments": parse_result["segments"],
        "chunks": chunks,
    }


def build_chunk_documents(chunks: list, *, embedding_provider: str | None = None) -> list[dict]:
    embeddings = None
    if embedding_provider is not None and chunks:
        embed_batch = get_batch_embedding_function(embedding_provider)
        embeddings = embed_batch([chunk.text for chunk in chunks])

    documents = []
    for index, chunk in enumerate(chunks):
        document = {
            "chunk_id": chunk.chunk_id,
            "video_id": chunk.video_id,
            "start": chunk.start,
            "end": chunk.end,
            "text": chunk.text,
        }

        if embeddings is not None:
            document[f"{embedding_provider}_embedding"] = embeddings[index]

        documents.append(document)

    return documents


def ingest_subtitle_chunks(
    *,
    video_id: str | None = None,
    subtitle_path: str | Path | None = None,
    max_duration: float = 60.0,
    max_words: int = 150,
    include_local_embeddings: bool = True,
    rebuild_index: bool = True,
) -> dict:
    chunk_result = chunk_subtitle(
        video_id=video_id,
        subtitle_path=subtitle_path,
        max_duration=max_duration,
        max_words=max_words,
    )

    documents = build_chunk_documents(
        chunk_result["chunks"],
        embedding_provider="local" if include_local_embeddings else None,
    )

    chunks_collection.delete_many({"video_id": chunk_result["video_id"]})

    if documents:
        chunks_collection.insert_many(documents)

    if rebuild_index and include_local_embeddings:
        rebuild_faiss_index()

    return {
        **chunk_result,
        "documents": documents,
    }


def generate_missing_embeddings(provider: str) -> int:
    field_name = f"{provider}_embedding"
    embed_batch = get_batch_embedding_function(provider)

    chunks_without_embeddings = list(
        chunks_collection.find(
            {field_name: {"$exists": False}},
            {"_id": 1, "text": 1},
        )
    )

    if not chunks_without_embeddings:
        return 0

    embeddings = embed_batch([chunk["text"] for chunk in chunks_without_embeddings])

    for chunk, embedding in zip(chunks_without_embeddings, embeddings):
        chunks_collection.update_one(
            {"_id": chunk["_id"]},
            {"$set": {field_name: embedding}},
        )

    return len(chunks_without_embeddings)


def load_index_manager() -> IndexManager:
    index_manager = IndexManager(FAISS_INDEX_PATH, FAISS_MAPPING_PATH)
    if not index_manager.load():
        raise FileNotFoundError(
            "FAISS index files were not found. Build or ingest embeddings first."
        )

    return index_manager


def run_search(
    query: str,
    *,
    top_k: int = 5,
    embedding_provider: str = "local",
) -> list[dict]:
    index_manager = load_index_manager()
    embed_function = get_single_embedding_function(embedding_provider)
    return retrieve_chunks(
        query,
        index_manager=index_manager,
        embed_function=embed_function,
        top_k=top_k,
    )
