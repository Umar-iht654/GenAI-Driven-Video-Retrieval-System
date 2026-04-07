// Import React hooks used to store and update the currently selected video segment
import { useEffect, useState } from 'react'

// Import the clickable timestamp card component
import TimestampCard from './TimestampCard'

// Import the video player component that plays the selected lecture segment
import VideoPlayer from './VideoPlayer'

// Define the component that renders one message in the chat
function Message({ message }) {
  // Get the timestamps from the message, or use an empty array if none are available
  const timestamps = message.timestamps ?? []

  // Store the currently selected segment and playback request for this message
  const [videoRequest, setVideoRequest] = useState(null)

  // Whenever the timestamps change, decide what the selected clip should be
  useEffect(() => {
    // If there are no timestamps, clear the selected video request
    if (timestamps.length === 0) {
      setVideoRequest(null)
      return
    }

    // Update the selected timestamp intelligently
    setVideoRequest((currentRequest) => {
      // If there is no currently selected segment yet, default to the first timestamp
      if (!currentRequest?.segment) {
        return {
          segment: timestamps[0],
          shouldPlaySegment: false,
          requestId: Date.now(),
        }
      }

      // Try to keep the currently selected timestamp if it still exists in the new list
      const nextSelectedTimestamp = timestamps.find(
        (timestamp) => timestamp.chunkId === currentRequest.segment.chunkId
      )

      // If the current selection still exists, keep it
      if (nextSelectedTimestamp) {
        return {
          ...currentRequest,
          segment: nextSelectedTimestamp,
        }
      }

      // Otherwise fall back to the first timestamp in the new list
      return {
        segment: timestamps[0],
        shouldPlaySegment: false,
        requestId: Date.now(),
      }
    })
  }, [timestamps])

  // Work out which timestamp is currently selected for this assistant response
  const selectedTimestamp = videoRequest?.segment ?? timestamps[0] ?? null

  // Use the preview text of the selected timestamp as the transcript snippet
  const selectedTranscript =
    selectedTimestamp?.preview?.trim() ||
    'No transcript snippet was returned for this retrieved chunk.'

  // Handle selecting a timestamp, with an optional instruction to start playback immediately
  const handleSelectTimestamp = (timestamp, shouldPlaySegment = false) => {
    setVideoRequest({
      segment: timestamp,
      shouldPlaySegment,
      requestId: Date.now(),
    })
  }

  // If this is a user message, render a simple user bubble
  if (message.role === 'user') {
    return (
      <article className="message message--user">
        <p className="message__label">You</p>
        <div className="message__bubble message__bubble--user">
          <p>{message.text}</p>
        </div>
      </article>
    )
  }

  // If this is a temporary loading message, render a loading-style assistant bubble
  if (message.loading) {
    return (
      <article className="message message--assistant">
        <p className="message__label">AI Response</p>
        <div className="message__bubble message__bubble--assistant">
          <p className="message__loading">Searching transcript chunks...</p>
        </div>
      </article>
    )
  }

  // Keep answer and summary as distinct fields in the assistant card
  const displayedAnswer = message.answer || 'No answer available.'
  const displayedSummary = message.summary || 'No summary available.'

  // Otherwise render a full assistant response with video, transcript, answer, summary, and timestamps
  return (
    <article className="message message--assistant">
      <p className="message__label">AI Response</p>

      {/* Add error styling if the backend request failed */}
      <div
        className={`message__bubble message__bubble--assistant${message.isError ? ' message__bubble--error' : ''}`}
      >
        {/* Show the video player only if there is a selected timestamp */}
        {selectedTimestamp ? (
          <VideoPlayer
            request={
              videoRequest ?? {
                segment: selectedTimestamp,
                shouldPlaySegment: false,
                requestId: 0,
              }
            }
          />
        ) : null}

        {/* Show the transcript snippet for the selected timestamp */}
        <div className="message__section">
          <h2>Transcript</h2>
          <p>{selectedTranscript}</p>
        </div>

        {/* Show the main answer text returned by the AI */}
        <div className="message__section">
          <h2>Answer</h2>
          <p>{displayedAnswer}</p>
        </div>

        {/* Show the summary text returned by the AI */}
        <div className="message__section">
          <h2>Summary</h2>
          <p>{displayedSummary}</p>
        </div>

        {/* Show the clickable timestamp cards */}
        <div className="message__section">
          <h2>Relevant Timestamps</h2>
          <p className="message__section-note">
            Click a timestamp to switch the clip preview for this answer card.
          </p>

          {timestamps.length > 0 ? (
            <div className="timestamp-list">
              {timestamps.map((timestamp) => (
                <TimestampCard
                  key={timestamp.chunkId}
                  timestamp={timestamp}
                  isSelected={timestamp.chunkId === selectedTimestamp?.chunkId}
                  onSelect={(selectedTimestampCard) =>
                    handleSelectTimestamp(selectedTimestampCard, false)
                  }
                  onPlaySegment={(selectedTimestampCard) =>
                    handleSelectTimestamp(selectedTimestampCard, true)
                  }
                />
              ))}
            </div>
          ) : (
            <p className="message__muted">
              No timestamp metadata was returned for this answer.
            </p>
          )}
        </div>
      </div>
    </article>
  )
}

// Export the component so ChatWindow.jsx can use it
export default Message
