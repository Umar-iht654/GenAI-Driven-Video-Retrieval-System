from pathlib import Path

# Import functions from the scripts I built before
from app.vttParser import parse_vtt_file
from app.chunker import chunk_segments
from app.db import chunks_collection

# Get project root
ROOT = Path(__file__).resolve().parents[2]

# Path to subtitle file
vtt_path = ROOT / "Data" / "subtitles" / "Lec1.vtt"

# Parse subtitles into segments
segments = parse_vtt_file(vtt_path)

# Convert segments into chunks
chunks = chunk_segments(
    segments,
    video_id="Lec1",
    max_duration=60,
    max_words=150
)

# Convert chunk objects into MongoDB documents
docs = []

for chunk in chunks:
    docs.append({
        "chunk_id": chunk.chunk_id,
        "video_id": chunk.video_id,
        "start": chunk.start,
        "end": chunk.end,
        "text": chunk.text
    })

# Insert documents into MongoDB
chunks_collection.insert_many(docs)

# Output how many chunks was inserted into db
print(f"Inserted {len(docs)} chunks into MongoDB")