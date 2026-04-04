// Format chat metadata so each sidebar item shows either creation time or message count plus timestamp
function formatChatMeta(chat) {
  // Format the chat creation date and time in a UK-style readable format
  const createdAtLabel = new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(chat.createdAt))

  // If the chat has no messages yet, show only the creation time
  if (chat.messages.length === 0) {
    return `Created ${createdAtLabel}`
  }

  // Build a correctly pluralised message count label
  const messageLabel = `${chat.messages.length} message${chat.messages.length === 1 ? '' : 's'}`

  // Return message count plus creation time for chats with content
  return `${messageLabel} | ${createdAtLabel}`
}

// Define the Sidebar component, which displays New Chat and the list of previous chats
function Sidebar({ chats, activeChatId, onNewChat, onSelectChat }) {
  return (
    // Sidebar container for chat navigation
    <aside className="sidebar">
      {/* Top area containing the workspace label and New Chat button */}
      <div className="sidebar__top">
        <p className="sidebar__eyebrow">Workspace</p>

        {/* Button that creates a fresh chat when clicked */}
        <button type="button" className="sidebar__new-chat" onClick={onNewChat}>
          New Chat
        </button>
      </div>

      {/* Main section for the chat history list */}
      <div className="sidebar__section">
        <p className="sidebar__heading">Chat History</p>

        {/* List of all chats stored in app state */}
        <ul className="sidebar__history">
          {chats.map((chat) => (
            <li key={chat.id}>
              {/* Each chat is rendered as a clickable button so the user can switch chats */}
              <button
                type="button"
                className={`sidebar__history-item${chat.id === activeChatId ? ' sidebar__history-item--active' : ''}`}
                onClick={() => onSelectChat(chat.id)}
              >
                {/* Show the chat title if it has messages, otherwise keep the default New Chat label */}
                <span>{chat.messages.length > 0 ? chat.title : 'New Chat'}</span>

                {/* Show chat metadata such as message count and creation time */}
                <small>{formatChatMeta(chat)}</small>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}

// Export this component so App.jsx can use it
export default Sidebar