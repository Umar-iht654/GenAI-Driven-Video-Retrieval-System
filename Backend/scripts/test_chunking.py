from pathlib import Path

from app.vttParser import parse_vtt_file
from app.chunker import chunk_segments

ROOT = Path(__file__).resolve().parents[2]
vtt_path = ROOT / "Data" / "subtitles" / "Lec1.vtt"

segments = parse_vtt_file(vtt_path)
chunks = chunk_segments(segments, video_id="Lec1", max_duration=60.0, max_words=150)

print(f"Parsed subtitle segments: {len(segments)}")
print(f"Created chunks: {len(chunks)}")
print()

for chunk in chunks[:3]:
    print(f"{chunk.chunk_id}")
    print(f"Start: {chunk.start:.2f} | End: {chunk.end:.2f}")
    print(f"Text: {chunk.text[:300]}")
    print("-" * 60)