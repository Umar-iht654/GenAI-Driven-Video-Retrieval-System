// Define the input area component used to type and submit questions
function InputBox({ value, onChange, onSubmit, isLoading }) {
  // Handle normal form submission from clicking the button or pressing Enter on the form
  const handleSubmit = (event) => {
    // Stop the browser from refreshing the page
    event.preventDefault()

    // Call the submit function passed in from App.jsx
    onSubmit()
  }

  // Handle keyboard behaviour inside the textarea
  const handleKeyDown = (event) => {
    // If Enter is pressed without Shift, submit instead of creating a new line
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSubmit()
    }
  }

  return (
    // Footer container for the input section at the bottom of the chat UI
    <footer className="input-box">
      {/* Form wrapper lets both button-click and Enter submission work naturally */}
      <form className="input-box__form" onSubmit={handleSubmit}>
        {/* Textarea lets the user type a question and optionally use Shift+Enter for multiple lines */}
        <textarea
          className="input-box__field"
          placeholder="Ask about a topic, explanation, or lecture moment..."
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />

        {/* Submit button is disabled while loading or if the input is empty */}
        <button
          type="submit"
          className="input-box__submit"
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? 'Asking...' : 'Submit'}
        </button>
      </form>

      {/* Small helper note shown below the input */}
      <p className="input-box__hint">
        Press Enter to send, Shift+Enter for a new line. Review answers carefully
        because AI can make mistakes.
      </p>
    </footer>
  )
}

// Export the component so App.jsx can use it
export default InputBox