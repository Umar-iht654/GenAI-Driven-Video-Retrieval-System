// Convert a numeric time in seconds into either mm:ss or h:mm:ss format
export function formatTimestamp(value) {
  const totalSeconds = Math.max(0, Math.floor(Number(value) || 0))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  // Use h:mm:ss if the value is at least one hour long
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  // Otherwise use mm:ss
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

// Convert a segment object into a range string like 02:45 - 03:12
export function formatSegmentRange(segment) {
  return `${formatTimestamp(segment.start)} - ${formatTimestamp(segment.end)}`
}

// Build a fallback chunk id if the backend did not provide one
function createFallbackChunkId(chunk, index) {
  return `${chunk?.video_id ?? 'lecture'}-${chunk?.start ?? 0}-${chunk?.end ?? 0}-${index}`
}

// Normalize one chunk into a consistent frontend timestamp object
function normalizeChunk(chunk, retrievedChunk, index) {
  const start = Number(chunk?.start ?? retrievedChunk?.start ?? 0)
  const end = Number(chunk?.end ?? retrievedChunk?.end ?? start)
  const safeEnd = end >= start ? end : start
  const videoId = chunk?.video_id ?? retrievedChunk?.video_id ?? 'Unknown lecture'

  return {
    chunkId:
      chunk?.chunk_id ??
      retrievedChunk?.chunk_id ??
      createFallbackChunkId(chunk ?? retrievedChunk, index),
    videoId,
    start,
    end: safeEnd,
    preview: retrievedChunk?.text_preview ?? chunk?.text_preview ?? '',
    distance: retrievedChunk?.distance ?? null,
  }
}

// Convert backend response chunks into a clean array of timestamp objects for the UI
export function normalizeTimestamps(response = {}) {
  const sourceChunks =
    response.chunks_used?.length > 0
      ? response.chunks_used
      : response.retrieved_chunks ?? []

  // Build a map of retrieved chunks so previews and distances can be attached easily
  const retrievedChunkMap = new Map(
    (response.retrieved_chunks ?? [])
      .filter((chunk) => chunk?.chunk_id)
      .map((chunk) => [chunk.chunk_id, chunk])
  )

  const seenChunkIds = new Set()

  return sourceChunks
    .map((chunk, index) =>
      normalizeChunk(
        chunk,
        chunk?.chunk_id ? retrievedChunkMap.get(chunk.chunk_id) : null,
        index
      )
    )
    .filter((chunk) => {
      // Remove duplicates and invalid chunk ids
      if (!chunk.chunkId || seenChunkIds.has(chunk.chunkId)) {
        return false
      }

      seenChunkIds.add(chunk.chunkId)
      return true
    })
    .slice(0, 4)
}