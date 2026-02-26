from pathlib import Path
from app.vttParser import parse_vtt_file

ROOT = Path(__file__).resolve().parents[2]
vtt_path = ROOT / "Data" / "subtitles" / "Lec1.vtt"

segments = parse_vtt_file(vtt_path)

print(f"Parsed segments: {len(segments)}")
print("First 3:")
for s in segments[:3]:
    print(f"- {s.start:.3f} -> {s.end:.3f}: {s.text[:80]}")