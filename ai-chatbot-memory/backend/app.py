"""
AI Chatbot with Conversation Memory (OpenAI-free)
Flask backend calling Ollama directly via HTTP.
Simplified version - no heavy dependencies.
"""

import os
import json
import requests
import re
import logging
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables from backend/.env (not dependent on cwd)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "neural-chat:7b")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").strip().lower() == "true"
MEMORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# In-memory conversation history (simple approach)
# ---------------------------------------------------------------------------
conversation_history = []

def save_memory():
    """Save conversation to JSON file."""
    try:
        with open(MEMORY_PATH, 'w') as f:
            json.dump(conversation_history, f, indent=2)
    except Exception as e:
        app.logger.error(f"Failed to save memory: {e}")

def load_memory():
    """Load conversation from JSON file. Create it if it does not exist."""
    global conversation_history
    if not os.path.exists(MEMORY_PATH):
        try:
            conversation_history = []
            with open(MEMORY_PATH, 'w') as f:
                json.dump(conversation_history, f, indent=2)
            app.logger.info("Initialized memory.json as it did not exist.")
        except Exception as e:
            app.logger.error(f"Failed to initialize memory file: {e}")
            conversation_history = []
    else:
        try:
            with open(MEMORY_PATH, 'r') as f:
                conversation_history = json.load(f)
        except Exception as e:
            app.logger.error(f"Failed to load memory: {e}")
            conversation_history = []

# Load memory on startup
load_memory()


def error_handler(f):
    """Decorator for consistent API error responses."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as exc:
            app.logger.exception("Request failed")
            return jsonify({"error": str(exc)}), 500

    return wrapper


def call_ollama(prompt: str) -> str:
    """Call Ollama API directly."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        app.logger.error(f"Ollama call failed: {e}")
        raise


def build_prompt(user_message: str) -> str:
    """Build a prompt with conversation context."""
    system_prompt = (
        "You are a helpful, friendly AI assistant named Shivani's Assistant. "
        "Respond naturally and conversationally. Be warm, helpful, and engaging. "
        "Provide complete, thoughtful responses. Answer questions directly and fully. "
        "Remember that you are a purely virtual AI assistant; do not suggest meeting up, "
        "having food/drinks in person, or any physical activities.\n\n"
    )
    
    # Include recent conversation context
    context = ""
    if len(conversation_history) > 0:
        context = "Recent conversation:\n"
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            context += f"{msg['role'].upper()}: {msg['content']}\n"
        context += "\n"
    
    return f"{system_prompt}{context}User: {user_message}\nAssistant:"


def extract_name(message: str) -> str:
    """
    Extract user name from message using regex patterns.
    Filters out common stop words to avoid false matches.
    """
    patterns = [
        r"\bmy name is\s+([a-zA-Z0-9\s\-'\u00C0-\u017F]+)",
        r"\bi am\s+([a-zA-Z0-9\s\-'\u00C0-\u017F]+)",
        r"\bi'm\s+([a-zA-Z0-9\s\-'\u00C0-\u017F]+)",
        r"\bcall me\s+([a-zA-Z0-9\s\-'\u00C0-\u017F]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Strip trailing/leading punctuation (e.g. periods, exclamation marks, question marks)
            name = name.strip(".,!?;: ")
            # Ignore common adjectives or helper words (stop words)
            stop_words = {
                "happy", "sad", "sorry", "tired", "excited", "good", "fine", 
                "ok", "okay", "here", "ready", "a", "an", "the", "not", 
                "hungry", "busy", "back", "again", "there", "well", "great"
            }
            if name.lower() not in stop_words:
                return name.title()
    return None


def find_stored_name() -> str:
    """
    Retrieve user name from conversation_history (memory.json) or ChromaDB if available.
    """
    # 1. Search in-memory conversation history (loaded from memory.json / populated in session) in reverse order
    for msg in reversed(conversation_history):
        if msg.get("role") == "user":
            extracted = extract_name(msg.get("content", ""))
            if extracted:
                return extracted

    # 2. Try querying ChromaDB if available and folder exists
    try:
        import chromadb
        chroma_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma")
        if os.path.exists(chroma_path):
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            collections = chroma_client.list_collections()
            for col_info in collections:
                collection = chroma_client.get_collection(name=col_info.name)
                results = collection.get()
                documents = results.get("documents", []) or []
                # Check documents in reverse
                for doc in reversed(documents):
                    # Try extraction on raw document
                    extracted = extract_name(doc)
                    if extracted:
                        return extracted
                    # Look for helper confirmation patterns inside ChromaDB documents
                    match = re.search(r"Nice to meet you, ([a-zA-Z0-9\s\-']+)", doc, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip()
                        name = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?]', '', name).strip()
                        if name.lower() not in {"you", "there", "again"}:
                            return name.title()
    except Exception as e:
        app.logger.debug(f"ChromaDB lookup skipped or failed: {e}")

    return None


def get_mock_response(user_message: str) -> str:
    """
    Return static response based on user input for mock deployment mode.
    """
    cleaned = user_message.strip().lower()

    # If the user asks for their name
    if (re.search(r"\bwhat\s+is\s+my\s+name\b", cleaned) or 
            re.search(r"\bwho\s+am\s+i\b", cleaned) or 
            re.search(r"\bdo\s+you\s+know\s+my\s+name\b", cleaned)):
        name = find_stored_name()
        if name:
            return f"Your name is {name}, based on my memory."
        else:
            return "I don't know your name yet. You can tell me by saying 'my name is [name]'."

    # If the user declares their name
    extracted_name = extract_name(user_message)
    if extracted_name:
        return f"Nice to meet you, {extracted_name}! I have stored your name in my memory."

    # Default static response
    return "This is a demo response. AI backend is in deployment mode."


def get_ai_response(user_message: str) -> str:
    """
    Generate response: Use Ollama if USE_OLLAMA=true; otherwise fallback to the mock system.
    """
    if USE_OLLAMA:
        app.logger.info("AI Chatbot Mode: OLLAMA MODE")
        prompt = build_prompt(user_message)
        return call_ollama(prompt)
    else:
        app.logger.info("AI Chatbot Mode: MOCK MODE")
        return get_mock_response(user_message)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Basic Ollama connectivity check."""
    ollama_ok = False
    ollama_error = None
    if USE_OLLAMA:
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            ollama_ok = r.status_code == 200
            if not ollama_ok:
                ollama_error = f"Unexpected status: {r.status_code}"
        except Exception as exc:
            ollama_error = str(exc)
    else:
        ollama_error = "Ollama disabled (MOCK MODE active)"

    return jsonify(
        {
            "status": "ok",
            "mode": "OLLAMA" if USE_OLLAMA else "MOCK",
            "chat_model": OLLAMA_CHAT_MODEL if USE_OLLAMA else "MockModel",
            "ollama_connected": ollama_ok,
            "ollama_error": ollama_error,
            "memory_type": "json-file",
        }
    )


@app.route("/chat", methods=["POST"])
@error_handler
def chat():
    """
    Chat flow:
    1. Receive user message
    2. Store message in memory
    3. Generate AI response (using Ollama or Mock fallback system)
    4. Store assistant reply
    5. Return JSON reply
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Step 1–2: store user message
    conversation_history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })

    # Step 3: Get response from Ollama or Mock Fallback system
    bot_reply = get_ai_response(user_message)

    # Step 4: persist assistant response
    conversation_history.append({
        "role": "assistant",
        "content": bot_reply,
        "timestamp": datetime.now().isoformat()
    })
    save_memory()

    # Step 5: return to frontend
    return jsonify({"reply": bot_reply})


@app.route("/reset", methods=["POST"])
@error_handler
def reset():
    """Clear conversation memory."""
    global conversation_history
    conversation_history = []
    save_memory()
    return jsonify({"message": "Conversation memory reset successfully"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
