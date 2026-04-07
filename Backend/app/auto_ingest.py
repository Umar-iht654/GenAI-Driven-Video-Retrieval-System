from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.chunker import chunk_segments
from app.db import chunks_collection
from app.embeddingFactory import get_batch_embedding_function
from app.faissIndex import (
    build_faiss_index,
    delete_faiss_artifacts,
    save_faiss_index,
    save_mapping,
)
from app.vttParser import parse_vtt_file
from scripts.transcribe import load_whisper_model, transcribe_video


# Lock ingestion and deletion work so only one pipeline update happens at a time.
# This keeps MongoDB, FAISS files, subtitles, and the manifest from drifting apart.
INGEST_LOCK = threading.Lock()

# Reuse one Whisper model instance for automatic ingestion.
# Whisper is expensive to load, so sharing one instance keeps repeated ingestion cheaper.
WHISPER_MODEL = None

# Build important project paths from this file location so the project remains portable.
ROOT = Path(__file__).resolve().parents[2]
VIDEOS_DIR = ROOT / "Data" / "videos"
SUBTITLES_DIR = ROOT / "Data" / "subtitles"
FAISS_DIR = ROOT / "Data" / "faiss"
FAISS_INDEX_PATH = FAISS_DIR / "local_index.faiss"
FAISS_MAPPING_PATH = FAISS_DIR / "local_mapping.json"

# Store processed-video state in a simple manifest file.
# This manifest is what prevents unchanged videos from being retranscribed on every startup.
MANIFEST_PATH = ROOT / "Data" / "ingestion_manifest.json"

# Use local embeddings for automatic ingestion so the watcher follows the same retrieval path
# as the rest of the backend.
embed_batch = get_batch_embedding_function("local")


# Get or create the Whisper model once.
# Both startup ingestion and watcher ingestion call this helper so they share the same model.
def get_whisper_model():
    global WHISPER_MODEL

    # Load the model only when it is first needed.
    if WHISPER_MODEL is None:
        WHISPER_MODEL = load_whisper_model(model_size="medium")

    # Return the shared model instance for reuse.
    return WHISPER_MODEL


# Read the current file modification time in a stable integer format.
# The manifest stores this value and compares it to the current file to detect real changes.
def get_video_mtime(video_path: Path) -> int:
    return int(video_path.stat().st_mtime_ns)


# Load the ingestion manifest from disk.
# This helper is defensive because the file may be missing, empty, or manually edited.
def load_ingestion_manifest() -> dict[str, dict]:
    # If the manifest does not exist yet, treat that as a fresh project state.
    if not MANIFEST_PATH.exists():
        return {}

    try:
        # Read the JSON manifest from disk.
        raw_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # If the manifest cannot be read, fall back to an empty manifest instead of crashing.
        print(f"[AUTO_INGEST] Manifest could not be read. Rebuilding from scratch. Error: {exc}")
        return {}

    # Ignore invalid top-level shapes and rebuild the manifest gradually from successful runs.
    if not isinstance(raw_manifest, dict):
        print("[AUTO_INGEST] Manifest file was not a JSON object. Rebuilding from scratch.")
        return {}

    normalized_manifest: dict[str, dict] = {}

    # Normalize each entry so later ingestion logic can rely on a consistent structure.
    for filename, entry in raw_manifest.items():
        if not isinstance(filename, str) or not isinstance(entry, dict):
            continue

        stored_mtime = entry.get("mtime")
        processed = bool(entry.get("processed"))

        if not isinstance(stored_mtime, (int, float)):
            continue

        normalized_manifest[filename] = {
            "mtime": int(stored_mtime),
            "processed": processed,
        }

    # Return the cleaned manifest.
    return normalized_manifest


# Save the manifest back to disk after successful ingestion or cleanup work.
# Writing readable JSON makes the file easy to inspect during demos and code reviews.
def save_ingestion_manifest(manifest: dict[str, dict]) -> None:
    # Ensure the Data directory exists before writing.
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Persist the manifest in a readable, deterministic format.
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# Decide whether a video should be ingested.
# A video is reprocessed only if it is new, previously failed, or has changed on disk.
def should_ingest_video(video_path: Path, manifest: dict[str, dict]) -> bool:
    manifest_entry = manifest.get(video_path.name)

    # New files are always ingested.
    if manifest_entry is None:
        return True

    # Failed or incomplete files should be retried.
    if not manifest_entry.get("processed", False):
        return True

    # Changed files should be reprocessed so transcript and FAISS data stay current.
    return manifest_entry.get("mtime") != get_video_mtime(video_path)


# Mark a video as successfully processed in the manifest.
# This write happens only after the full pipeline succeeds, which is what prevents
# unchanged files from being retranscribed on future startups.
def mark_video_as_processed(video_path: Path, manifest: dict[str, dict]) -> None:
    manifest[video_path.name] = {
        "mtime": get_video_mtime(video_path),
        "processed": True,
    }
    save_ingestion_manifest(manifest)


# Rebuild the FAISS index from all chunks currently stored in MongoDB.
# This keeps FAISS aligned with the transcript data after ingestion or deletion.
def rebuild_faiss_index() -> bool:
    # Ensure the FAISS output folder exists before writing files.
    FAISS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all chunks that already have local embeddings because those are the vectors
    # that should be searchable in FAISS.
    chunks = list(
        chunks_collection.find(
            {"local_embedding": {"$exists": True}},
            {
                "_id": 1,
                "chunk_id": 1,
                "video_id": 1,
                "local_embedding": 1,
            },
        )
    )

    # If no embedded chunks remain, remove FAISS files entirely so stale search data
    # cannot survive after videos are deleted.
    if not chunks:
        delete_faiss_artifacts(FAISS_INDEX_PATH, FAISS_MAPPING_PATH)
        print("[AUTO_INGEST] No embedded chunks found, cleared FAISS files.")
        return False

    embeddings = []
    mapping = []

    # Build the vector list and the FAISS-to-Mongo mapping together so each FAISS row
    # can be traced back to a transcript chunk document.
    for position, chunk in enumerate(chunks):
        embeddings.append(chunk["local_embedding"])
        mapping.append(
            {
                "faiss_position": position,
                "mongo_id": str(chunk["_id"]),
                "chunk_id": chunk["chunk_id"],
                "video_id": chunk["video_id"],
            }
        )

    # Write the fresh index and mapping files to disk.
    index = build_faiss_index(embeddings)
    save_faiss_index(index, FAISS_INDEX_PATH)
    save_mapping(mapping, FAISS_MAPPING_PATH)

    print(f"[AUTO_INGEST] FAISS rebuilt with {len(chunks)} chunks.")
    return True


# Remove stale transcript/index/manifest data for a video that no longer exists.
# This handles deleted and renamed files so search does not keep returning missing videos.
def remove_deleted_video(video_path: Path, reload_search_state=None) -> None:
    # Serialize cleanup with ingestion so shared state is updated safely.
    with INGEST_LOCK:
        manifest = load_ingestion_manifest()
        video_id = video_path.stem

        # Remove transcript chunks for the missing video from MongoDB.
        delete_result = chunks_collection.delete_many({"video_id": video_id})

        # Remove any stale subtitle file with the same stem.
        subtitle_path = SUBTITLES_DIR / f"{video_id}.vtt"
        subtitle_removed = subtitle_path.exists()
        subtitle_path.unlink(missing_ok=True)

        # Remove the matching manifest entry because the source file no longer exists.
        manifest_removed = manifest.pop(video_path.name, None) is not None

        # Save the manifest only when it changed.
        if manifest_removed:
            save_ingestion_manifest(manifest)

        # Rebuild FAISS only when transcript data was actually removed.
        if delete_result.deleted_count > 0:
            rebuild_faiss_index()

            # Reload the in-memory search state if the running app provided a callback.
            if reload_search_state is not None:
                reload_search_state()

        # Log the cleanup so deletion behaviour is visible during debugging.
        if manifest_removed or delete_result.deleted_count > 0 or subtitle_removed:
            print(
                "[AUTO_INGEST] Removed deleted video data for "
                f"{video_path.name} (chunks={delete_result.deleted_count}, "
                f"manifest_removed={manifest_removed}, subtitle_removed={subtitle_removed})."
            )


# Synchronize the manifest with the current contents of Data/videos.
# This is mainly used during startup so old manifest entries from deleted or renamed videos
# are cleaned up before the app scans for videos to ingest.
def sync_deleted_videos(reload_search_state=None) -> None:
    # Ensure the videos folder exists so startup works cleanly on a fresh project.
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_ingestion_manifest()
    current_video_names = {video_path.name for video_path in VIDEOS_DIR.glob("*.mp4")}

    # Any manifest entry that points to a missing file should be removed.
    missing_video_names = [
        filename for filename in manifest.keys() if filename not in current_video_names
    ]

    for filename in missing_video_names:
        remove_deleted_video(VIDEOS_DIR / filename, reload_search_state=reload_search_state)


# Ingest one single lecture video end-to-end.
# The manifest check happens inside this function so startup ingestion and watcher ingestion
# share exactly the same decision logic.
def ingest_video(video_path: Path, reload_search_state=None) -> None:
    # Ignore files that disappeared before the worker could process them.
    if not video_path.exists():
        return

    # Ignore non-mp4 files because the pipeline is designed for lecture videos only.
    if video_path.suffix.lower() != ".mp4":
        return

    video_id = video_path.stem
    subtitle_path = SUBTITLES_DIR / f"{video_id}.vtt"

    # Serialize the full ingestion pipeline so duplicate events cannot run overlapping
    # transcribe/index writes.
    with INGEST_LOCK:
        manifest = load_ingestion_manifest()

        # Skip unchanged files completely.
        # This is the key change that prevents startup from retranscribing everything.
        if not should_ingest_video(video_path, manifest):
            print(f"[AUTO_INGEST] Skipping unchanged video: {video_path.name}")
            return

        print(f"[AUTO_INGEST] Starting ingestion for {video_path.name}")

        # Step 1: Transcribe the video into a VTT subtitle file.
        # This is the slowest part of the pipeline, so avoiding unnecessary runs matters.
        model = get_whisper_model()
        transcribe_video(video_path, model)

        # Step 2: Parse the VTT subtitles into timestamped transcript segments.
        segments = parse_vtt_file(subtitle_path)

        # Step 3: Chunk the parsed transcript into searchable sections.
        chunks = chunk_segments(segments, video_id=video_id)

        # If chunking produced nothing, do not mark the file as processed.
        # Leaving the manifest unchanged allows the file to be retried later.
        if not chunks:
            print(f"[AUTO_INGEST] No chunks created for {video_id}, skipping.")
            return

        # Step 4: Generate local embeddings for each chunk.
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embed_batch(chunk_texts)

        # Step 5: Remove any older chunks for the same lecture so re-ingestion replaces them cleanly.
        chunks_collection.delete_many({"video_id": video_id})

        # Step 6: Insert the fresh chunks into MongoDB.
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            documents.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "video_id": chunk.video_id,
                    "start": chunk.start,
                    "end": chunk.end,
                    "text": chunk.text,
                    "local_embedding": embedding,
                }
            )

        chunks_collection.insert_many(documents)
        print(f"[AUTO_INGEST] Inserted {len(documents)} chunks for {video_id}.")

        # Step 7: Rebuild FAISS so the new lecture content becomes searchable immediately.
        rebuild_faiss_index()

        # Step 8: Update the manifest only after the whole pipeline succeeded.
        # This is where the manifest file is written after successful ingestion.
        mark_video_as_processed(video_path, manifest)

        # Step 9: Reload the in-memory search state if the running app provided a callback.
        if reload_search_state is not None:
            reload_search_state()

        print(f"[AUTO_INGEST] Finished ingestion for {video_id}.")


# Process all videos already present in the folder when the backend starts.
# Startup still scans every file, but the manifest-aware ingest_video() function now ensures
# only new or changed videos are actually reprocessed.
def ingest_existing_videos(reload_search_state=None) -> None:
    # Ensure the videos directory exists so startup works cleanly even on a fresh checkout.
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # First remove stale manifest/data entries for deleted or renamed videos.
    sync_deleted_videos(reload_search_state=reload_search_state)

    # Then ingest only the videos that are new or changed.
    for video_path in sorted(VIDEOS_DIR.glob("*.mp4")):
        ingest_video(video_path, reload_search_state=reload_search_state)


# Watchdog handler that reacts when files are created, modified, or deleted in Data/videos.
# The handler deduplicates repeated events, waits for files to finish copying, and then
# hands off to the same manifest-aware ingestion functions used during startup.
class VideoFolderHandler(FileSystemEventHandler):
    # Store the reload callback and the set of currently scheduled file paths.
    # The scheduled set is what prevents duplicate create/modify events from starting
    # multiple ingestion runs for the same file at the same time.
    def __init__(self, reload_search_state=None):
        super().__init__()
        self.reload_search_state = reload_search_state
        self._scheduled_paths: set[str] = set()
        self._state_lock = threading.Lock()

    # Normalize a file path to one stable string form so different filesystem events
    # for the same file collapse to the same dedupe key.
    def _normalize_path(self, path: str) -> str:
        return str(Path(path).resolve(strict=False))

    # Check whether a path is still scheduled.
    # This lets background workers stop early if the file was deleted before ingestion started.
    def _is_path_scheduled(self, normalized_path: str) -> bool:
        with self._state_lock:
            return normalized_path in self._scheduled_paths

    # Wait until a file becomes stable before starting ingestion.
    # A file is treated as stable when its size and mtime stop changing across consecutive checks.
    def _wait_for_stable_file(
        self,
        normalized_path: str,
        video_path: Path,
        check_interval: float = 1.0,
        stable_checks_required: int = 2,
        timeout_seconds: float = 300.0,
    ) -> bool:
        deadline = time.time() + timeout_seconds
        last_signature = None
        stable_checks = 0

        while time.time() < deadline:
            # If the path was unscheduled, another event such as deletion cancelled this work.
            if not self._is_path_scheduled(normalized_path):
                return False

            # If the file does not exist yet, keep waiting.
            if not video_path.exists():
                stable_checks = 0
                last_signature = None
                time.sleep(check_interval)
                continue

            # Use size + mtime together as a practical signal that a copy has finished.
            stat = video_path.stat()
            current_signature = (stat.st_size, stat.st_mtime_ns)

            if stat.st_size > 0 and current_signature == last_signature:
                stable_checks += 1
                if stable_checks >= stable_checks_required:
                    return True
            else:
                stable_checks = 0
                last_signature = current_signature

            time.sleep(check_interval)

        # If the file never stabilized, log and skip this attempt.
        print(f"[AUTO_INGEST] Timed out waiting for stable file: {video_path.name}")
        return False

    # Run the background ingestion worker for one path.
    # This wraps the stability check, manifest-aware ingestion, and cleanup of the scheduled set.
    def _process_ingest(self, path: str) -> None:
        normalized_path = self._normalize_path(path)
        video_path = Path(normalized_path)

        try:
            # Stop early if the file never stabilized or was cancelled/deleted.
            if not self._wait_for_stable_file(normalized_path, video_path):
                return

            # Hand off to the shared ingestion pipeline.
            ingest_video(video_path, reload_search_state=self.reload_search_state)
        except Exception as exc:
            # Log watcher failures explicitly because background-thread exceptions can be easy to miss.
            print(f"[AUTO_INGEST] Failed to ingest {video_path.name}: {exc}")
        finally:
            # Always clear the scheduled flag so future events for the same file can run again.
            with self._state_lock:
                self._scheduled_paths.discard(normalized_path)

    # Queue a new ingestion worker only if the path is not already queued or running.
    def _schedule_ingest(self, path: str) -> None:
        video_path = Path(path)

        # Ignore non-mp4 files because the ingestion pipeline is designed for lecture videos only.
        if video_path.suffix.lower() != ".mp4":
            return

        normalized_path = self._normalize_path(path)

        with self._state_lock:
            # Ignore duplicate create/modify events while the same path is already queued.
            if normalized_path in self._scheduled_paths:
                return

            self._scheduled_paths.add(normalized_path)

        # Start the background worker so the watchdog event loop stays responsive.
        threading.Thread(
            target=self._process_ingest,
            args=(normalized_path,),
            daemon=True,
        ).start()

    # Handle deletion events by cancelling queued ingestion and removing stale data.
    # This keeps the manifest, MongoDB, and FAISS in sync if a processed video is removed.
    def _handle_deleted_video(self, path: str) -> None:
        normalized_path = self._normalize_path(path)

        # Cancel any queued processing for the deleted file before cleanup starts.
        with self._state_lock:
            self._scheduled_paths.discard(normalized_path)

        # Run cleanup in a background thread so the watchdog loop is not blocked.
        threading.Thread(
            target=remove_deleted_video,
            args=(Path(normalized_path), self.reload_search_state),
            daemon=True,
        ).start()

    # React to new files by scheduling manifest-aware ingestion.
    def on_created(self, event) -> None:
        if not event.is_directory:
            self._schedule_ingest(event.src_path)

    # React to file modifications in the same way.
    # Repeated modify events are safely deduplicated by _schedule_ingest().
    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._schedule_ingest(event.src_path)

    # React to file deletions by removing stale transcript/index/manifest data.
    def on_deleted(self, event) -> None:
        if not event.is_directory:
            self._handle_deleted_video(event.src_path)


# Start the folder watcher that listens for new, changed, and deleted videos.
# The watcher uses the same manifest-aware ingestion logic as startup, so behaviour
# stays consistent regardless of how a file enters the system.
def start_video_watcher(reload_search_state=None) -> Observer:
    # Ensure the watched directory exists before starting watchdog.
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(
        VideoFolderHandler(reload_search_state=reload_search_state),
        str(VIDEOS_DIR),
        recursive=False,
    )
    observer.start()

    print(f"[AUTO_INGEST] Watching folder: {VIDEOS_DIR}")
    return observer


# Stop the folder watcher cleanly during backend shutdown.
# Joining the observer prevents background filesystem threads from being left behind.
def stop_video_watcher(observer: Observer | None) -> None:
    if observer is None:
        return

    observer.stop()
    observer.join(timeout=5)
