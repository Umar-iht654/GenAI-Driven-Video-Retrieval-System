// Define the localStorage key used to save the chat state in the browser
const CHAT_STORAGE_KEY = 'ai-video-retrieval.chat-state'

// Clean and validate one saved message before restoring it from localStorage
function sanitizeMessage(message, index) {
  // If the message is not a valid object, ignore it
  if (!message || typeof message !== 'object') {
    return null
  }

  // Return a safe normalized message object with defaults for missing or invalid fields
  return {
    id:
      typeof message.id === 'string'
        ? message.id
        : `restored-message-${Date.now()}-${index}`,
    role: message.role === 'assistant' ? 'assistant' : 'user',
    text: typeof message.text === 'string' ? message.text : '',
    answer: typeof message.answer === 'string' ? message.answer : '',
    summary: typeof message.summary === 'string' ? message.summary : '',
    timestamps: Array.isArray(message.timestamps) ? message.timestamps : [],
    isError: Boolean(message.isError),
  }
}

// Clean and validate one saved chat before restoring it from localStorage
function sanitizeChat(chat, index) {
  // If the chat is not a valid object, ignore it
  if (!chat || typeof chat !== 'object') {
    return null
  }

  // Restore and sanitize the messages array if it exists
  const messages = Array.isArray(chat.messages)
    ? chat.messages
        .map((message, messageIndex) =>
          sanitizeMessage(message, `${index}-${messageIndex}`)
        )
        .filter(Boolean)
    : []

  // Return a safe normalized chat object
  return {
    id: typeof chat.id === 'string' ? chat.id : `restored-chat-${index}`,
    title:
      typeof chat.title === 'string' && chat.title.trim()
        ? chat.title
        : 'New Chat',
    messages,
    createdAt:
      typeof chat.createdAt === 'string'
        ? chat.createdAt
        : new Date().toISOString(),
  }
}

// Load chat state from localStorage and fall back to a fresh chat if nothing valid exists
export function loadChatState(createChat) {
  // If running somewhere without a browser window, create a fallback chat
  if (typeof window === 'undefined') {
    const fallbackChat = createChat()

    return {
      chats: [fallbackChat],
      activeChatId: fallbackChat.id,
    }
  }

  try {
    // Read the saved JSON string from localStorage
    const storedState = window.localStorage.getItem(CHAT_STORAGE_KEY)

    // If nothing was stored, force fallback behaviour
    if (!storedState) {
      throw new Error('No stored chat state found.')
    }

    // Parse the saved JSON string into an object
    const parsedState = JSON.parse(storedState)

    // Restore and sanitize the chats array
    const chats = Array.isArray(parsedState?.chats)
      ? parsedState.chats.map(sanitizeChat).filter(Boolean)
      : []

    // If no valid chats were restored, force fallback behaviour
    if (chats.length === 0) {
      throw new Error('Stored chats were empty or invalid.')
    }

    // Restore the active chat id if valid, otherwise default to the first restored chat
    const activeChatId =
      typeof parsedState?.activeChatId === 'string' &&
      chats.some((chat) => chat.id === parsedState.activeChatId)
        ? parsedState.activeChatId
        : chats[0].id

    return { chats, activeChatId }
  } catch {
    // If anything fails, create one fresh fallback chat
    const fallbackChat = createChat()

    return {
      chats: [fallbackChat],
      activeChatId: fallbackChat.id,
    }
  }
}

// Save the current chat state to localStorage
export function persistChatState(chats, activeChatId) {
  // If no browser window exists, do nothing
  if (typeof window === 'undefined') {
    return
  }

  try {
    // Save chats and activeChatId as JSON in localStorage
    window.localStorage.setItem(
      CHAT_STORAGE_KEY,
      JSON.stringify({ chats, activeChatId })
    )
  } catch (error) {
    // Log an error if saving fails
    console.error('Unable to save chat history to localStorage.', error)
  }
}