// Import a helper that formats the start and end time of a segment nicely
import { formatSegmentRange } from '../utils/timestamps'

// Define the timestamp card component used inside the assistant answer card
function TimestampCard({ timestamp, isSelected, onSelect, onPlaySegment }) {
  // Allow keyboard interaction so Enter or Space also selects the timestamp card
  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onSelect(timestamp)
    }
  }

  return (
    // Main clickable timestamp card container
    <div
      className={`timestamp-card${isSelected ? ' timestamp-card--selected' : ''}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelect(timestamp)}
      onKeyDown={handleKeyDown}
      aria-pressed={isSelected}
    >
      {/* Left side of the card containing metadata and preview text */}
      <div className="timestamp-card__content">
        <div className="timestamp-card__meta">
          <p className="timestamp-card__title">{timestamp.videoId}</p>
          <p className="timestamp-card__time">{formatSegmentRange(timestamp)}</p>
        </div>

        {/* Show a short preview of the retrieved transcript snippet if available */}
        {timestamp.preview ? (
          <p className="timestamp-card__preview">
            {timestamp.preview.length > 90
              ? `${timestamp.preview.slice(0, 87).trim()}...`
              : timestamp.preview}
          </p>
        ) : (
          <p className="timestamp-card__preview timestamp-card__preview--muted">
            Click to load this lecture moment in the player.
          </p>
        )}
      </div>

      {/* Button for immediately loading and playing the selected clip */}
      <button
        type="button"
        className="timestamp-card__button"
        onClick={(event) => {
          // Stop the outer card click so the play button can trigger a separate action
          event.stopPropagation()
          onPlaySegment(timestamp)
        }}
      >
        Play clip
      </button>
    </div>
  )
}

// Export the component so Message.jsx can use it
export default TimestampCard