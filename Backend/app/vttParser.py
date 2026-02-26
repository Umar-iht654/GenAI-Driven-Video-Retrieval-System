from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional


# Regex pattern to dect lines like
# 00:01.500 --> 00:04.000
# captures start timestamp & end timestamp
TIMING_LINE_RE = re.compile(
    r"^\s*(?P<start>\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}(?::\d{2})?\.\d{3})(?:\s+.*)?\s*$"
)


# Dataclass to represent one subtitle segment
# start and end are in seconds (float)
# text is the full caption text for that time window
@dataclass(frozen=True)
class VTTSegment:
    start: float
    end: float
    text: str


# Convert timestamp string to seconds
# e.g. 1:23.500 to 83.5
# Accepts:
# MM:SS.mmm
# HH:MM:SS.mmm
def _timestamp_to_seconds(ts: str) -> float:
    parts = ts.split(":")

    # Format: MM:SS.mmm
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    # Format: HH:MM:SS.mmm
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"Invalid VTT timestamp: {ts}")


# Parse raw VTT text into structured segments
def parse_vtt_text(vtt_text: str) -> List[VTTSegment]:

    # Normalize line endings for consistency
    lines = vtt_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    segments: List[VTTSegment] = []
    i = 0

    # Remove BOM if present
    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    # Skip WEBVTT header
    if i < len(lines) and lines[i].strip().startswith("WEBVTT"):
        i += 1
        # Skip header metadata until blank line
        while i < len(lines) and lines[i].strip() != "":
            i += 1
        # Skip blank lines
        while i < len(lines) and lines[i].strip() == "":
            i += 1

    # Helper to skip NOTE / STYLE / REGION blocks
    def skip_block(start_index: int) -> int:
        j = start_index
        while j < len(lines) and lines[j].strip() != "":
            j += 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        return j

    while i < len(lines):

        line = lines[i].strip()

        # Skip empty lines
        if line == "":
            i += 1
            continue

        # Skip metadata blocks
        if line.startswith("NOTE") or line.startswith("STYLE") or line.startswith("REGION"):
            i = skip_block(i)
            continue

        timing_match = TIMING_LINE_RE.match(lines[i])
        cue_id: Optional[str] = None

        # If this line is not a timing line, check if next line is
        if not timing_match:
            if i + 1 < len(lines) and TIMING_LINE_RE.match(lines[i + 1]):
                cue_id = lines[i].strip()
                i += 1
                timing_match = TIMING_LINE_RE.match(lines[i])

        # If still no timing match, skip this line
        if not timing_match:
            i += 1
            continue

        # Extract start and end timestamps
        start_ts = timing_match.group("start")
        end_ts = timing_match.group("end")

        # Convert timestamps to float seconds
        start_s = _timestamp_to_seconds(start_ts)
        end_s = _timestamp_to_seconds(end_ts)

        # Move to caption text lines
        i += 1
        text_lines: List[str] = []

        # Collect all lines until next blank line
        while i < len(lines) and lines[i].strip() != "":
            text_lines.append(lines[i].rstrip())
            i += 1

        # Join multi-line captions into one string
        text = " ".join(t.strip() for t in text_lines).strip()

        # Only store non-empty segments
        if text:
            segments.append(VTTSegment(start=start_s, end=end_s, text=text))

        # Skip trailing blank lines
        while i < len(lines) and lines[i].strip() == "":
            i += 1

    return segments


# Read file from disk and parse it
def parse_vtt_file(path: Path) -> List[VTTSegment]:
    vtt_text = path.read_text(encoding="utf-8", errors="replace")
    return parse_vtt_text(vtt_text)