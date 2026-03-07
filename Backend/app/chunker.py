from dataclasses import dataclass
from typing import List

# Import from the vtt parser I built before
from app.vttParser import VTTSegment

# Dataclass to represent one chunk of transcript
@dataclass(frozen=True)
class TranscriptChunk:
    chunk_id: str
    video_id: str
    start: float
    end: float
    text: str

# Function to count words in a piece of text
def count_words(text: str) -> int:
    return len(text.split())

# Merge subtitle segments into larger chunks
def chunk_segments(
    segments: List[VTTSegment],
    video_id: str,
    max_duration: float = 60.0,
    max_words: int = 150,
) -> List[TranscriptChunk]:

    chunks: List[TranscriptChunk] = []

    # These hold the current chunk being built
    current_text_parts: List[str] = []
    current_start: float | None = None
    current_end: float | None = None
    current_word_count = 0
    chunk_index = 1

    for segment in segments:
        segment_text = segment.text.strip()

        # Skip empty subtitle lines just in case
        if not segment_text:
            continue

        segment_word_count = count_words(segment_text)

        # If this is the first segment in the chunk, initialize chunk start/end
        if current_start is None:
            current_start = segment.start
            current_end = segment.end
            current_text_parts = [segment_text]
            current_word_count = segment_word_count
            continue

        # Calculate what the duration would be if we add this segment
        proposed_duration = segment.end - current_start

        # Calculate what the word count would be if we add this segment
        proposed_word_count = current_word_count + segment_word_count

        # If adding this segment would make the chunk too large, save current chunk first
        if proposed_duration > max_duration or proposed_word_count > max_words:
            chunk_text = " ".join(current_text_parts).strip()

            chunks.append(
                TranscriptChunk(
                    chunk_id=f"{video_id}_{chunk_index:04d}",
                    video_id=video_id,
                    start=current_start,
                    end=current_end if current_end is not None else current_start,
                    text=chunk_text,
                )
            )

            # Start a new chunk with the current segment
            chunk_index += 1
            current_start = segment.start
            current_end = segment.end
            current_text_parts = [segment_text]
            current_word_count = segment_word_count
        else:
            # Otherwise keep building the current chunk
            current_text_parts.append(segment_text)
            current_end = segment.end
            current_word_count = proposed_word_count

    # Save the final chunk if one is being built
    if current_start is not None and current_text_parts:
        chunk_text = " ".join(current_text_parts).strip()

        chunks.append(
            TranscriptChunk(
                chunk_id=f"{video_id}_{chunk_index:04d}",
                video_id=video_id,
                start=current_start,
                end=current_end if current_end is not None else current_start,
                text=chunk_text,
            )
        )

    return chunks