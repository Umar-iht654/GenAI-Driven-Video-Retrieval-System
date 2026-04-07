
import { useEffect, useRef } from 'react'

// Import the component that renders each individual message
import Message from './Message'

// Define the main chat display area component
function ChatWindow({
  activeChatId,
  chatTitle,
  messages,
  isLoading,
}) {
  // Create a ref so we can directly control the scrolling of the messages container
  const messagesRef = useRef(null)

  // Auto-scroll to the bottom whenever the active chat changes, messages change, or loading state changes
  useEffect(() => {
    // If the messages container does not exist yet, do nothing
    if (!messagesRef.current) {
      return
    }

    // Scroll smoothly to the bottom so the newest message is visible
    messagesRef.current.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [activeChatId, messages.length, isLoading])

  return (
    // Main container for the chat window
    <section className="chat-window">
      {/* Header at the top of the chat window */}
      <header className="chat-window__header">
        {/* Small app label shown above the chat title */}
        <p className="chat-window__eyebrow">AI Video Retrieval</p>

        {/* Current chat title, which is either "New Chat" or based on the first user message */}
        <h1>{chatTitle}</h1>

        {/* Short description of what the chat system does */}
        <p className="chat-window__subtitle">
          Ask questions about your indexed videos and review the timestamps used
          to support each answer.
        </p>
      </header>

      {/* Scrollable area containing the conversation */}
      <div className="chat-window__messages" ref={messagesRef}>
        {/* Show the empty-state card only when there are no messages and nothing is loading */}
        {messages.length === 0 && !isLoading ? (
          <div className="chat-window__empty">
            <p className="chat-window__empty-title">Start with a question</p>
            <p>
              Try asking for a concept explanation, a recap, or where a topic
              appears in a lecture.
            </p>
          </div>
        ) : null}

        {/* Render each saved message in the chat */}
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {/* Show a temporary loading assistant message while waiting for the backend */}
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

// Export the component so App.jsx can use it
export default ChatWindow