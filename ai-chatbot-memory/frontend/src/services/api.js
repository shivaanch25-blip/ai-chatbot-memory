/**
 * Backend API client – async fetch wrappers for chat and reset endpoints.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }

  return data;
}

/**
 * Send a user message and return the bot reply text.
 * @param {string} message
 * @returns {Promise<string>}
 */
export async function sendMessage(message) {
  const data = await request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  return data.reply;
}

/**
 * Reset server-side conversation memory (Chroma collection).
 * @returns {Promise<void>}
 */
export async function resetConversation() {
  await request("/reset", { method: "POST" });
}
