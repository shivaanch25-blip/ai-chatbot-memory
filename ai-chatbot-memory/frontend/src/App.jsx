import ChatBox from "./components/ChatBox.jsx";

/**
 * Root application – renders the chat interface.
 */
export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Chatbot Memory</h1>
        <p className="subtitle">Semantic memory powered by ChromaDB + LangChain</p>
      </header>
      <ChatBox />
    </div>
  );
}
