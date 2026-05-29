import { useEffect, useRef, useState } from "react";
import { sendMessage, resetConversation } from "../services/api.js";

/**
 * Main chat UI: message list, input, loading state, auto-scroll, reset.
 */
export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const reply = await sendMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = async () => {
    if (loading) return;
    setError(null);
    try {
      await resetConversation();
      setMessages([]);
    } catch (err) {
      setError(err.message || "Failed to reset conversation");
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-toolbar">
        <button
          type="button"
          className="btn-reset"
          onClick={handleReset}
          disabled={loading}
        >
          Reset memory
        </button>
      </div>

      <div className="messages-window" role="log" aria-live="polite">
        {messages.length === 0 && !loading && (
          <p className="empty-state">Send a message to start the conversation.</p>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.role === "user" ? "message-user" : "message-bot"}`}
          >
            <span className="message-label">
              {msg.role === "user" ? "You" : "Bot"}
            </span>
            <p className="message-content">{msg.content}</p>
          </div>
        ))}

        {loading && (
          <div className="message message-bot message-loading">
            <span className="message-label">Bot</span>
            <p className="message-content">
              <span className="typing-indicator">Thinking</span>
              <span className="dots">...</span>
            </p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && <p className="error-banner">{error}</p>}

      <div className="input-row">
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          aria-label="Chat message input"
        />
        <button
          type="button"
          className="btn-send"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
