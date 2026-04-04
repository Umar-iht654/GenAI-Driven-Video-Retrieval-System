// Define the InputBox component, which handles the user's text input and submit button
function InputBox({ value, onChange, onSubmit, isLoading }) {
  // Prevent the browser's default form submission and call the custom submit handler instead
  const handleSubmit = (event) => {
    event.preventDefault()
    onSubmit()
  }

  return (
    // Footer container for the input area at the bottom of the chat panel
    <footer className="input-box">
      {/* Form wrapper so pressing Enter also submits the question */}
      <form className="input-box__form" onSubmit={handleSubmit}>
        {/* Text input where the user types a question */}
        <input
          type="text"
          className="input-box__field"
          placeholder="Ask about a topic, explanation, or lecture moment..."
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={isLoading}
        />

        {/* Submit button that changes label while the system is waiting for a backend response */}
        <button
          type="submit"
          className="input-box__submit"
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? 'Asking...' : 'Submit'}
        </button>
      </form>

      {/* Small helper note under the input field reminding the user to verify answers */}
      <p className="input-box__hint">Make sure to review answers as this Ai can make mistakes.</p>
    </footer>
  )
}

// Export this component so App.jsx can use it
export default InputBox