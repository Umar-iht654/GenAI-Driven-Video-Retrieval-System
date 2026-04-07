import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import InputBox from './components/InputBox'
import { loadChatState, persistChatState } from './utils/chatStorage'
import { normalizeTimestamps } from './utils/timestamps'
import './App.css'

//Sets the number of transcript chunks to ask the backend for by default.
const DEFAULT_TOP_K = 3

// Create a unique id for chats and messages using crypto if available, otherwise use a fallback
function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`
}

// Create a brand new empty chat object with an id, default title, empty messages, and timestamp
function createChat() {
  return {
    id: createId(),
    title: 'New Chat',
    messages: [],
    createdAt: new Date().toISOString(),
  }
}

// Generate a chat title from the user's first message so the sidebar reflects the topic of the chat
function createChatTitle(messageText) {
  // Remove repeated whitespace and trim the text so the title looks neat
  const normalizedText = messageText.replace(/\s+/g, ' ').trim()

  // If the message has no usable content, keep the default title
  if (!normalizedText) {
    return 'New Chat'
  }

  // If the message is short enough, use it directly as the title
  if (normalizedText.length <= 48) {
    return normalizedText
  }

  // If the message is too long, shorten it and add ellipsis
  return `${normalizedText.slice(0, 45).trim()}...`
}

// Build a short fallback summary if an older backend response does not include one yet
function extractSummary(answer = '') {
  // Clean up whitespace to make sentence splitting more reliable
  const normalizedAnswer = answer.replace(/\s+/g, ' ').trim()

  // Return fallback text if no answer exists
  if (!normalizedAnswer) {
    return 'No summary available.'
  }

  // Take the first one or two sentences of the answer as the summary
  const firstThought = normalizedAnswer
    .split(/(?<=[.!?])\s+/)
    .slice(0, 2)
    .join(' ')

  // If the extracted summary is short enough, return it directly
  if (firstThought.length <= 180) {
    return firstThought
  }

  // Otherwise trim it to a shorter readable length
  return `${firstThought.slice(0, 177).trim()}...`
}

function updateChatAndMoveToTop(chats, targetChatId, updateChat) {
  const updatedChats = chats.map((chat) =>
    chat.id === targetChatId ? updateChat(chat) : chat
  )

  const targetChat = updatedChats.find((chat) => chat.id === targetChatId)
  const remainingChats = updatedChats.filter((chat) => chat.id !== targetChatId)

  return targetChat ? [targetChat, ...remainingChats] : updatedChats
}

function deleteChatAndResolveState(chats, activeChatId, chatIdToDelete, createChat) {
  const remainingChats = chats.filter((chat) => chat.id !== chatIdToDelete)

  if (remainingChats.length === 0) {
    const freshChat = createChat()

    return {
      chats: [freshChat],
      activeChatId: freshChat.id,
    }
  }

  return {
    chats: remainingChats,
    activeChatId:
      activeChatId === chatIdToDelete || !remainingChats.some((chat) => chat.id === activeChatId)
        ? remainingChats[0].id
        : activeChatId,
  }
}

// Main React component for the frontend application
function App() {
  const [initialChatState] = useState(() => loadChatState(createChat))

  // Store all chat sessions in state and begin with the restored chat history if it exists
  const [chats, setChats] = useState(initialChatState.chats)

  // Track which chat is currently open in the main panel
  const [activeChatId, setActiveChatId] = useState(initialChatState.activeChatId)

  // Track the current contents of the message input field
  const [inputValue, setInputValue] = useState('')

  // Track which chat is currently waiting for a backend response
  const [pendingChatId, setPendingChatId] = useState(null)

  // Find the active chat object from the chats array and fall back to the first chat if needed
  const activeChat = chats.find((chat) => chat.id === activeChatId) ?? chats[0]

  // Check if any request is currently in progress
  const isLoading = pendingChatId !== null

  // Check specifically if the currently visible chat is the one loading
  const isActiveChatLoading = pendingChatId === activeChat?.id

  useEffect(() => {
    if (!chats.some((chat) => chat.id === activeChatId) && chats[0]) {
      setActiveChatId(chats[0].id)
    }
  }, [activeChatId, chats])

  useEffect(() => {
    if (!activeChat?.id) {
      return
    }

    persistChatState(chats, activeChatId ?? activeChat.id)
  }, [activeChat?.id, activeChatId, chats])

  // Switch to a different chat when the user clicks it in the sidebar
  const handleSelectChat = (chatId) => {
    setActiveChatId(chatId)
    setInputValue('')
  }

  // Create a new chat while preserving every previous conversation
  const handleNewChat = () => {
    // Build a fresh empty chat object
    const newChat = createChat()

    // Add the new chat to the top of the chat list
    setChats((currentChats) => [newChat, ...currentChats])

    // Switch the UI to the newly created chat
    setActiveChatId(newChat.id)

    // Clear the input box for the fresh conversation
    setInputValue('')
  }

  // Delete a chat, keep history persisted, and always leave the UI with a valid active chat
  const handleDeleteChat = (chatId) => {
    const nextState = deleteChatAndResolveState(chats, activeChatId, chatId, createChat)

    setChats(nextState.chats)
    setActiveChatId(nextState.activeChatId)
    setPendingChatId((currentPendingChatId) =>
      currentPendingChatId === chatId ? null : currentPendingChatId
    )

    if (activeChatId === chatId) {
      setInputValue('')
    }
  }

  // Handle sending a user question to the backend and appending the response to the active chat
  const handleSubmit = async () => {
    // Remove extra whitespace so empty or accidental input is ignored
    const question = inputValue.trim()

    // Stop submission if the input is empty, another request is already running, or there is no active chat
    if (!question || isLoading || !activeChat) {
      return
    }

    // Store the active chat id now so state updates do not accidentally target the wrong chat later
    const targetChatId = activeChat.id

    // Create the user message object that will be appended to the chat immediately
    const userMessage = {
      id: createId(),
      role: 'user',
      text: question,
    }

    // Add the user's message to the correct chat and update the chat title if it is the first message
    setChats((currentChats) =>
      updateChatAndMoveToTop(currentChats, targetChatId, (chat) => ({
        ...chat,
        title: chat.messages.length === 0 ? createChatTitle(question) : chat.title,
        messages: [...chat.messages, userMessage],
      }))
    )

    // Clear the input box after submission
    setInputValue('')

    // Mark this chat as the one currently waiting for a backend response
    setPendingChatId(targetChatId)

    try {
      // Send the question to the backend ask endpoint
      const response = await fetch('/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          top_k: DEFAULT_TOP_K,
        }),
      })

      // Throw an error if the backend returned a bad HTTP status
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      // Parse the JSON response from the backend
      const payload = await response.json()

      // Build the assistant message using the backend answer, summary, and timestamps
      const assistantMessage = {
        id: createId(),
        role: 'assistant',
        answer: payload.answer,
        summary:
          typeof payload.summary === 'string' && payload.summary.trim()
            ? payload.summary
            : extractSummary(payload.answer),
        timestamps: normalizeTimestamps(payload),
      }

      // Append the assistant response to the same chat the user asked in
      setChats((currentChats) =>
        updateChatAndMoveToTop(currentChats, targetChatId, (chat) => ({
          ...chat,
          messages: [...chat.messages, assistantMessage],
        }))
      )
    } catch (error) {
      // Create a fallback assistant message if the backend request fails
      const fallbackMessage = {
        id: createId(),
        role: 'assistant',
        answer:
          'I could not get a response from the backend. Check that FastAPI is running on http://127.0.0.1:8000 and try again.',
        summary: 'The request to /ask failed before a valid answer was returned.',
        timestamps: [],
        isError: true,
      }

      // Append the fallback error response to the active chat so the user sees feedback in the UI
      setChats((currentChats) =>
        updateChatAndMoveToTop(currentChats, targetChatId, (chat) => ({
          ...chat,
          messages: [...chat.messages, fallbackMessage],
        }))
      )

      // Log the real error in the browser console for debugging
      console.error(error)
    } finally {
      // Clear loading state once the request finishes, but only if this is still the active pending chat
      setPendingChatId((currentPendingChatId) =>
        currentPendingChatId === targetChatId ? null : currentPendingChatId
      )
    }
  }

  // Render the full frontend layout with sidebar, main chat window, and input box
  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        activeChatId={activeChat?.id}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
      />

      <main className="chat-panel">
        <ChatWindow
          activeChatId={activeChat?.id}
          chatTitle={activeChat?.messages.length ? activeChat.title : 'New Chat'}
          messages={activeChat?.messages ?? []}
          isLoading={isActiveChatLoading}
        />
        <InputBox
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </main>
    </div>
  )
}

// Export the App component so main.jsx can render it
export default App
