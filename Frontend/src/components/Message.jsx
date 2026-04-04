// Convert a numeric time in seconds into a human-readable format like mm:ss or h:mm:ss
function formatTime(value) {
  // Convert the input to a safe whole number of seconds and prevent negative values
  const totalSeconds = Math.max(0, Math.floor(Number(value) || 0))

  // Calculate the number of hours in the timestamp
  const hours = Math.floor(totalSeconds / 3600)

  // Calculate the number of minutes remaining after removing full hours
  const minutes = Math.floor((totalSeconds % 3600) / 60)

  // Calculate the number of remaining seconds
  const seconds = totalSeconds % 60

  // If the timestamp includes at least one hour, return h:mm:ss format
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  // Otherwise return mm:ss format
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

// Define the Message component, which renders one user, loading, or assistant message
function Message({ message }) {
  // Get the timestamps array from the message, or use an empty array if none exist
  const timestamps = message.timestamps ?? []

  // If the message belongs to the user, show a simple user chat bubble
  if (message.role === 'user') {
    return (
      <article className="message message--user">
        {/* Small label showing that this message came from the user */}
        <p className="message__label">You</p>

        {/* User message bubble */}
        <div className="message__bubble message__bubble--user">
          <p>{message.text}</p>
        </div>
      </article>
    )
  }

  // If the message is a temporary loading state, show a loading bubble instead of an answer
  if (message.loading) {
    return (
      <article className="message message--assistant">
        {/* Label showing this is an AI message */}
        <p className="message__label">AI Response</p>

        {/* Assistant bubble containing loading text */}
        <div className="message__bubble message__bubble--assistant">
          <p className="message__loading">Searching transcript chunks...</p>
        </div>
      </article>
    )
  }

  // Otherwise render a full assistant response with answer, summary, and timestamps
  return (
    <article className="message message--assistant">
      {/* Label showing the message came from the AI */}
      <p className="message__label">AI Response</p>

      {/* Assistant bubble with optional error styling if the message represents a failed request */}
      <div
        className={`message__bubble message__bubble--assistant${message.isError ? ' message__bubble--error' : ''}`}
      >
        {/* Section showing the full answer returned to the user */}
        <div className="message__section">
          <h2>Answer</h2>
          <p>{message.answer}</p>
        </div>

        {/* Section showing the shorter summary extracted from the answer */}
        <div className="message__section">
          <h2>Summary</h2>
          <p>{message.summary}</p>
        </div>

        {/* Section showing the relevant timestamps returned from the backend */}
        <div className="message__section">
          <h2>Relevant Timestamps</h2>

          {/* If timestamps exist, render them as cards */}
          {timestamps.length > 0 ? (
            <div className="timestamp-list">
              {timestamps.map((timestamp) => (
                <div className="timestamp-card" key={timestamp.chunk_id}>
                  <div>
                    {/* Lecture or video name */}
                    <p className="timestamp-card__title">{timestamp.video_id}</p>

                    {/* Start and end time for the retrieved chunk */}
                    <p className="timestamp-card__time">
                      {formatTime(timestamp.start)} - {formatTime(timestamp.end)}
                    </p>
                  </div>

                  {/* Placeholder button for later timestamp navigation */}
                  <button type="button" className="timestamp-card__button">
                    Go to timestamp
                  </button>
                </div>
              ))}
            </div>
          ) : (
            // If no timestamps exist, show fallback text
            <p className="message__muted">
              No timestamp metadata was returned for this answer.
            </p>
          )}
        </div>
      </div>
    </article>
  )
}

// Export this component so ChatWindow.jsx can use it
export default Message