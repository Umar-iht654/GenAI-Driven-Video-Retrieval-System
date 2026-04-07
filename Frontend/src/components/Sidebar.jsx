// Import React hooks for state, lifecycle effects, and DOM element references
import { useEffect, useRef, useState } from 'react'

// Import createPortal so the popup menu can be rendered outside the sidebar container
import { createPortal } from 'react-dom'

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
function Sidebar({ chats, activeChatId, onNewChat, onSelectChat, onDeleteChat }) {
  // Track which chat currently has its 3-dot menu open
  const [openMenuChatId, setOpenMenuChatId] = useState(null)

  // Store the screen position where the popup menu should appear
  const [menuPosition, setMenuPosition] = useState(null)

  // Reference to the whole sidebar DOM element
  const sidebarRef = useRef(null)

  // Reference to the popup menu DOM element
  const menuRef = useRef(null)

  // Store references to each 3-dot menu button by chat id
  const menuButtonRefs = useRef(new Map())

  // Save or remove a menu button DOM reference for a specific chat
  const setMenuButtonRef = (chatId, element) => {
    // If the element exists, store it in the map
    if (element) {
      menuButtonRefs.current.set(chatId, element)
      return
    }

    // If the element is gone, remove it from the map
    menuButtonRefs.current.delete(chatId)
  }

  // Calculate and update the popup menu position based on the clicked 3-dot button
  const updateMenuPosition = (chatId) => {
    // Find the stored button element for this chat
    const button = menuButtonRefs.current.get(chatId)

    // If there is no button or the app is not running in a browser, clear the position
    if (!button || typeof window === 'undefined') {
      setMenuPosition(null)
      return
    }

    // Get the button's position relative to the viewport
    const rect = button.getBoundingClientRect()

    // Set an estimated popup width so placement can be calculated cleanly
    const menuWidth = 230

    // Set an estimated popup height so placement stays inside the viewport
    const estimatedMenuHeight = 170

    // Keep some spacing from the edges of the viewport
    const viewportPadding = 12

    // Position the popup horizontally so it stays inside the viewport
    const left = Math.min(
      window.innerWidth - menuWidth - viewportPadding,
      Math.max(viewportPadding, rect.right - menuWidth + 6)
    )

    // Position the popup vertically below the button where possible
    const top = Math.min(
      window.innerHeight - estimatedMenuHeight - viewportPadding,
      rect.bottom + 10
    )

    // Save the final popup position into state
    setMenuPosition({
      left,
      top: Math.max(viewportPadding, top),
    })
  }

  // Add document-level listeners so clicking outside or pressing Escape closes the popup menu
  useEffect(() => {
    function handlePointerDown(event) {
      // Get the currently open menu button element if a chat menu is open
      const menuButton = openMenuChatId
        ? menuButtonRefs.current.get(openMenuChatId)
        : null

      // Ignore clicks inside the popup menu or on the menu button itself
      if (menuRef.current?.contains(event.target) || menuButton?.contains(event.target)) {
        return
      }

      // If the click is completely outside the sidebar, close the menu
      if (!sidebarRef.current?.contains(event.target)) {
        setOpenMenuChatId(null)
        return
      }

      // Otherwise also close the menu for general outside clicks within the sidebar area
      setOpenMenuChatId(null)
    }

    function handleEscapeKey(event) {
      // Close the popup if the user presses Escape
      if (event.key === 'Escape') {
        setOpenMenuChatId(null)
      }
    }

    // Listen for outside clicks
    document.addEventListener('mousedown', handlePointerDown)

    // Listen for Escape key presses
    document.addEventListener('keydown', handleEscapeKey)

    // Remove listeners when the component updates or unmounts
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleEscapeKey)
    }
  }, [openMenuChatId])

  // Recalculate the popup position whenever the open menu changes or the page is resized/scrolled
  useEffect(() => {
    // If no menu is open, clear the stored position
    if (!openMenuChatId) {
      setMenuPosition(null)
      return
    }

    // Position the menu immediately
    updateMenuPosition(openMenuChatId)

    // Create a handler that repositions the menu on resize or scroll
    const handleRepositionMenu = () => updateMenuPosition(openMenuChatId)

    // Reposition on window resize
    window.addEventListener('resize', handleRepositionMenu)

    // Reposition on any scroll event, including nested containers
    window.addEventListener('scroll', handleRepositionMenu, true)

    // Clean up listeners when the menu closes or component unmounts
    return () => {
      window.removeEventListener('resize', handleRepositionMenu)
      window.removeEventListener('scroll', handleRepositionMenu, true)
    }
  }, [openMenuChatId])

  // Open or close the menu when the 3-dot button is clicked
  const handleToggleMenu = (event, chatId) => {
    // Stop the click from bubbling up and accidentally selecting the chat
    event.stopPropagation()

    // If this chat's menu is already open, close it
    if (openMenuChatId === chatId) {
      setOpenMenuChatId(null)
      return
    }

    // Otherwise calculate the menu position and open the popup
    updateMenuPosition(chatId)
    setOpenMenuChatId(chatId)
  }

  // Delete the selected chat from the sidebar
  const handleDelete = (event, chatId) => {
    // Stop the click from bubbling up
    event.stopPropagation()

    // Close the popup menu first
    setOpenMenuChatId(null)

    // Call the delete handler passed in from App.jsx
    onDeleteChat(chatId)
  }

  // Find the currently open chat object so the popup can display its title
  const openMenuChat = chats.find((chat) => chat.id === openMenuChatId) ?? null

  return (
    // Sidebar container for chat navigation
    <aside className="sidebar" ref={sidebarRef}>
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
              <div
                className={`sidebar__history-item${chat.id === activeChatId ? ' sidebar__history-item--active' : ''}`}
              >
                {/* Main clickable area of the chat card used to switch chats */}
                <button
                  type="button"
                  className="sidebar__history-main"
                  onClick={() => {
                    // Close any open menu when switching chats
                    setOpenMenuChatId(null)

                    // Notify the parent component to switch to this chat
                    onSelectChat(chat.id)
                  }}
                >
                  {/* Show the chat title if it has messages, otherwise keep the default New Chat label */}
                  <span>{chat.messages.length > 0 ? chat.title : 'New Chat'}</span>

                  {/* Show chat metadata such as message count and creation time */}
                  <small>{formatChatMeta(chat)}</small>
                </button>

                {/* Container for the 3-dot actions button */}
                <div className="sidebar__history-actions">
                  <button
                    type="button"
                    className="sidebar__history-menu-button"
                    ref={(element) => setMenuButtonRef(chat.id, element)}
                    aria-label={`Open actions for ${chat.messages.length > 0 ? chat.title : 'New Chat'}`}
                    aria-haspopup="menu"
                    aria-expanded={openMenuChatId === chat.id}
                    onClick={(event) => handleToggleMenu(event, chat.id)}
                  >
                    {/* Render a 3-dot icon using three spans */}
                    <span className="sidebar__history-menu-icon" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </span>
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Render the popup menu outside the sidebar layout using a portal so it is not clipped by scrolling/overflow */}
      {openMenuChatId && menuPosition && typeof document !== 'undefined'
        ? createPortal(
            <div className="sidebar__history-menu-layer">
              <div
                ref={menuRef}
                className="sidebar__history-menu"
                role="menu"
                style={{
                  top: `${menuPosition.top}px`,
                  left: `${menuPosition.left}px`,
                }}
              >
                {/* Popup header showing the type of menu and the selected chat name */}
                <div className="sidebar__history-menu-header">
                  <p className="sidebar__history-menu-title">Chat actions</p>
                  <p className="sidebar__history-menu-caption">
                    {openMenuChat?.messages.length > 0 ? openMenuChat.title : 'New Chat'}
                  </p>
                </div>

                {/* Visual divider between the popup header and actions */}
                <div className="sidebar__history-menu-divider" />

                {/* Popup action list */}
                <div className="sidebar__history-menu-list">
                  <button
                    type="button"
                    className="sidebar__history-menu-item sidebar__history-menu-item--danger"
                    role="menuitem"
                    onClick={(event) => handleDelete(event, openMenuChatId)}
                  >
                    <span className="sidebar__history-menu-item-label">Delete chat</span>
                    <span className="sidebar__history-menu-item-hint">
                      Remove this conversation
                    </span>
                  </button>
                </div>
              </div>
            </div>,
            // Render the popup menu directly into document.body so it floats above the sidebar
            document.body
          )
        : null}
    </aside>
  )
}

// Export this component so App.jsx can use it
export default Sidebar