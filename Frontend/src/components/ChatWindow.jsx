// Import the Message component so each chat message can be rendered consistently
import Message from './Message'

// Define the ChatWindow component, which shows the chat header and message area
function ChatWindow({ chatTitle, messages, isLoading }) {
  return (
    // Main container for the chat window section
    <section className="chat-window">
      {/* Header area that shows the app label, chat title, and short description */}
      <header className="chat-window__header">
        {/* Small label above the main title */}
        <p className="chat-window__eyebrow">AI Video Retrieval</p>

        {/* Current chat title, such as "New Chat" or the first question */}
        <h1>{chatTitle}</h1>

        {/* Subtitle explaining what the app does */}
        <p className="chat-window__subtitle">
          Ask questions about your indexed videos and review the timestamps used
          to support each answer.
        </p>
      </header>

      {/* Scrollable message area that displays chat messages and loading state */}
      <div className="chat-window__messages">
        {/* Show an empty-state card only when there are no messages and the app is not loading */}
        {messages.length === 0 && !isLoading ? (
          <div className="chat-window__empty">
            {/* Title of the empty state */}
            <p className="chat-window__empty-title">Start with a question</p>

            {/* Hint text suggesting what kind of questions the user can ask */}
            <p>
              Try asking for a concept explanation, a recap, or where a topic
              appears in a lecture.
            </p>
          </div>
        ) : null}

        {/* Loop through all messages and render each one using the Message component */}
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {/* If the app is loading, show a temporary assistant loading message */}
        {isLoading ? (
          <Message
            message={{
              id: 'loading-message',
              role: 'assistant',
              loading: true,
            }}
          />
        ) : null}
      </div>
    </section>
  )
}

// Export this component so App.jsx can use it
export default ChatWindow