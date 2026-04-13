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

# Build one transcript chunk object from collected values
def build_chunk(
    video_id: str,
    chunk_index: int,
    text_parts: List[str],
    start: float,
    end: float,
) -> TranscriptChunk:
    return TranscriptChunk(
        chunk_id=f"{video_id}_{chunk_index:04d}",
        video_id=video_id,
        start=start,
        end=end,
        text=" ".join(text_parts).strip(),
    )


# Merge subtitle segments into smaller overlapping transcript chunks
def chunk_segments(
    segments: List[VTTSegment],
    video_id: str,
    max_duration: float = 35.0,
    max_words: int = 100,
    overlap_segments: int = 2,
) -> List[TranscriptChunk]:
    # Final list of transcript chunks that will be returned
    chunks: List[TranscriptChunk] = []

    # Store the raw subtitle segments currently being collected into one chunk
    current_segments: List[VTTSegment] = []

    # Store the text from the current chunk being built
    current_text_parts: List[str] = []

    # Track the start time of the current chunk
    current_start: float | None = None

    # Track the end time of the current chunk
    current_end: float | None = None

    # Track the current total word count of the chunk
    current_word_count = 0

    # Chunk numbering starts at 1
    chunk_index = 1

    # Go through every subtitle segment in order
    for segment in segments:
        # Clean the subtitle text
        segment_text = segment.text.strip()

        # Skip empty subtitle lines just in case
        if not segment_text:
            continue

        # Count words in the current segment
        segment_word_count = count_words(segment_text)

        # If this is the first segment of a new chunk, initialize the chunk
        if current_start is None:
            current_segments = [segment]
            current_text_parts = [segment_text]
            current_start = segment.start
            current_end = segment.end
            current_word_count = segment_word_count
            continue

        # Calculate what the chunk duration would become if we add this segment
        proposed_duration = segment.end - current_start

        # Calculate what the chunk word count would become if we add this segment
        proposed_word_count = current_word_count + segment_word_count

        # If adding this segment makes the chunk too large, close the current chunk first
        if proposed_duration > max_duration or proposed_word_count > max_words:
            # Save the finished chunk
            chunks.append(
                build_chunk(
                    video_id=video_id,
                    chunk_index=chunk_index,
                    text_parts=current_text_parts,
                    start=current_start,
                    end=current_end if current_end is not None else current_start,
                )
            )

            # Move to the next chunk number
            chunk_index += 1

            # Keep the last few segments from the previous chunk as overlap
            # This helps when a concept spans a chunk boundary
            overlap = current_segments[-overlap_segments:] if overlap_segments > 0 else []

            # Start the next chunk using the overlap plus the current segment
            current_segments = overlap + [segment]

            # Rebuild the text list from the overlapping segments
            current_text_parts = [seg.text.strip() for seg in current_segments if seg.text.strip()]

            # Reset chunk timing using the new current segment window
            current_start = current_segments[0].start
            current_end = current_segments[-1].end

            # Recalculate word count from the new overlapping chunk contents
            current_word_count = sum(
                count_words(seg.text.strip())
                for seg in current_segments
                if seg.text.strip()
            )
        else:
            # Otherwise keep growing the current chunk
            current_segments.append(segment)
            current_text_parts.append(segment_text)
            current_end = segment.end
            current_word_count = proposed_word_count

    # After the loop, save the final chunk if there is one being built
    if current_start is not None and current_text_parts:
        chunks.append(
            build_chunk(
                video_id=video_id,
                chunk_index=chunk_index,
                text_parts=current_text_parts,
                start=current_start,
                end=current_end if current_end is not None else current_start,
            )
        )

    # Return all built transcript chunks
    return chunks