import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Find the root HTML element and render the App component into it
createRoot(document.getElementById('root')).render(
  // Wrap the app in StrictMode to help detect unsafe React patterns during development
  <StrictMode>
    <App />
  </StrictMode>,
)
