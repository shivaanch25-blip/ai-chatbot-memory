# AI Chatbot Memory

Full-stack chatbot with **semantic conversation memory** using React (Vite), Flask, LangChain, local Ollama, and ChromaDB.

User message
↓
Frontend (React - Vercel)
↓ API call
Backend (Flask - Render)
↓
IF local:
Ollama LLM (chat + embeddings)
ELSE:
Mock fallback system

- ChromaDB memory (if available)

## Folder structure

```
ai-chatbot-memory/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env
│   └── chroma/          # auto-created persistent vector DB
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── styles.css
        ├── components/ChatBox.jsx
        └── services/api.js
```

## Prerequisites

- **Python 3.10–3.12** (recommended for stable ChromaDB binary compatibility, especially on Windows)
- **Node.js 18+**
- **Ollama** (optional for local development only)
- Cloud deployment works without Ollama using fallback mode

## Setup & run

### 1. Backend

```bash
cd ai-chatbot-memory/backend

# Create virtual environment (recommended)
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
# source venv/bin/activate

pip install -r requirements.txt
```

Edit `.env` and set your Ollama models:

```env
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
```

Ollama model defaults: `llama3.1` (chat) and `nomic-embed-text` (embeddings).
If you want to use different models, update the values in `backend/.env`.

If models aren't downloaded yet, run (in PowerShell):

```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
```

Start the Flask server:

```bash
python app.py
```

Backend runs at **http://localhost:5000**

| Endpoint  | Method | Description                                   |
| --------- | ------ | --------------------------------------------- |
| `/chat`   | POST   | `{ "message": "..." }` → `{ "reply": "..." }` |
| `/reset`  | POST   | Clears Chroma conversation memory             |
| `/health` | GET    | Health check                                  |

### 2. Frontend

Open a **new terminal**:

```bash
cd ai-chatbot-memory/frontend

npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

Optional: set a custom API URL in `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000
```

## Usage

1. Open **http://localhost:5173** in your browser.
2. Type a message and click **Send** (or press Enter).
3. The bot uses retrieved past messages as context for each reply.
4. Click **Reset memory** to clear the ChromaDB collection.

## Environment variables (backend)

| Variable             | Required | Default                  | Description                       |
| -------------------- | -------- | ------------------------ | --------------------------------- |
| `OLLAMA_BASE_URL`    | No       | `http://localhost:11434` | Ollama server URL                 |
| `OLLAMA_CHAT_MODEL`  | No       | `llama3.1`               | Chat model name (for replies)     |
| `OLLAMA_EMBED_MODEL` | No       | `nomic-embed-text`       | Embedding model name (for memory) |

User message
↓
Frontend (React - Vercel)
↓ API call
Backend (Flask - Render)
↓
IF local:
Ollama LLM (chat + embeddings)
ELSE:
Mock fallback system

- ChromaDB memory (if available)

## 🌐 Deployment

### Backend (Flask API)

- Hosted on: Render
- Mode: Hybrid (Ollama locally, Mock fallback in cloud)

Base URL:
https://ai-chatbot-memory-3.onrender.com

### Frontend (React)

- Hosted on: Vercel

Live App:
https://ai-chatbot-memory-psi.vercel.app/

## Troubleshooting

- **Ollama connection error** — Make sure Ollama is installed, running, and the models exist:
  - `ollama serve`
  - `ollama pull llama3.1`
  - `ollama pull nomic-embed-text`
- **CORS errors** — Ensure the backend is running on port 5000 before opening the frontend.
- **Empty / weak memory** — Send a few messages first; retrieval improves as Chroma accumulates embeddings.
- **Chroma errors after reset** — The `chroma/` folder is recreated automatically; you can delete `backend/chroma/` manually if needed.
- **NumPy / Chroma import errors on Windows** — If you're using Python 3.14+, recreate the venv with Python 3.10–3.12 (delete `backend/venv` first), then reinstall dependencies.

## Tech stack

| Layer     | Technology                            |
| --------- | ------------------------------------- |
| Frontend  | React 18, Vite                        |
| Backend   | Flask, flask-cors                     |
| AI        | LangChain, Ollama (chat + embeddings) |
| Vector DB | ChromaDB (local persistent)           |

## 🔥 Hybrid AI System

This project supports a production-safe hybrid architecture:

- Local Mode → Uses Ollama for real LLM inference
- Cloud Mode → Automatically switches to mock fallback system
- Memory persists via JSON + ChromaDB (if available)

This ensures the system works both locally and in cloud deployments without breaking.

## 🚀 Features

- Full-stack AI chatbot (React + Flask)
- Semantic memory using ChromaDB
- Local LLM integration via Ollama
- Hybrid deployment (local + cloud fallback)
- Persistent conversation memory
- REST API backend
- Production-ready deployment (Render + Vercel)
