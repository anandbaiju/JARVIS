/* ══════════════════════════════════════════════════════════════
   J.A.R.V.I.S — Frontend Application Logic
   SSE streaming chat, voice, system controls
   ══════════════════════════════════════════════════════════════ */

const API = "http://localhost:8000";

// ── DOM References ───────────────────────────────────────────────

const chatMessages  = document.getElementById("chat-messages");
const chatInput     = document.getElementById("chat-input");
const typingIndicator = document.getElementById("typing-indicator");
const statusDot     = document.getElementById("status-dot");
const statusLabel   = document.getElementById("status-label");
const modelPill     = document.getElementById("model-pill");
const clockEl       = document.getElementById("clock");
const btnMic        = document.getElementById("btn-mic");
const panelStatus   = document.getElementById("panel-status");
const panelModel    = document.getElementById("panel-model");
const panelUser     = document.getElementById("panel-user");

// ── State ────────────────────────────────────────────────────────

let isStreaming = false;
let isRecording = false;

// ── Utilities ────────────────────────────────────────────────────

function getTimeString() {
    const now = new Date();
    return now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function showTyping() {
    typingIndicator.classList.add("active");
    scrollToBottom();
}

function hideTyping() {
    typingIndicator.classList.remove("active");
}

// ── Clock ────────────────────────────────────────────────────────

function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}
setInterval(updateClock, 1000);
updateClock();

// Set welcome message time
document.getElementById("welcome-time").textContent = getTimeString();

// ── Startup Sound ────────────────────────────────────────────────

function playStartupTone() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const notes = [523.25, 659.25, 783.99]; // C5, E5, G5 — ascending triad
        const duration = 0.15;

        notes.forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = "sine";
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.08, ctx.currentTime + i * duration);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + (i + 1) * duration + 0.1);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(ctx.currentTime + i * duration);
            osc.stop(ctx.currentTime + (i + 1) * duration + 0.15);
        });
    } catch (e) {
        // Web Audio not available — silent fallback
    }
}

// ── Status Check ─────────────────────────────────────────────────

async function checkStatus() {
    try {
        const res = await fetch(`${API}/status`);
        const data = await res.json();

        if (data.ollama_online) {
            statusDot.classList.add("online");
            statusLabel.textContent = "ONLINE";
            panelStatus.textContent = "CONNECTED";
            panelStatus.style.color = "#00FF88";
        } else {
            statusDot.classList.remove("online");
            statusLabel.textContent = "OLLAMA OFFLINE";
            panelStatus.textContent = "LLM OFFLINE";
            panelStatus.style.color = "#FF3D3D";
        }

        modelPill.textContent = data.model || "—";
        panelModel.textContent = data.model || "—";
        panelUser.textContent = data.user || "—";

    } catch (e) {
        statusDot.classList.remove("online");
        statusLabel.textContent = "BACKEND OFFLINE";
        panelStatus.textContent = "DISCONNECTED";
        panelStatus.style.color = "#FF3D3D";
        modelPill.textContent = "—";
    }
}

// ── Message Rendering ────────────────────────────────────────────

function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user-message";
    div.innerHTML = `
        <span class="msg-prefix">YOU:</span>
        <span class="msg-text">${escapeHtml(text)}</span>
        <span class="msg-time">${getTimeString()}</span>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function createJarvisMessage() {
    const div = document.createElement("div");
    div.className = "message jarvis-message";
    div.innerHTML = `
        <span class="msg-prefix">› JARVIS:</span>
        <span class="msg-text"></span>
        <span class="msg-time">${getTimeString()}</span>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
    return div.querySelector(".msg-text");
}

function addJarvisMessage(text) {
    const textEl = createJarvisMessage();
    typewriterEffect(textEl, text);
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Typewriter Effect ────────────────────────────────────────────

function typewriterEffect(element, text, speed = 18) {
    let index = 0;
    element.textContent = "";

    function type() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            scrollToBottom();
            setTimeout(type, speed);
        }
    }
    type();
}

// ── SSE Streaming Chat ──────────────────────────────────────────

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isStreaming) return;

    chatInput.value = "";
    addUserMessage(message);
    showTyping();
    isStreaming = true;

    try {
        const textEl = createJarvisMessage();
        hideTyping();

        const encodedMsg = encodeURIComponent(message);
        const response = await fetch(`${API}/chat/stream?message=${encodedMsg}`);

        if (!response.ok) {
            textEl.textContent = "Sir, the backend returned an error. Check the server logs.";
            isStreaming = false;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE lines
            const lines = buffer.split("\n");
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;

                try {
                    const payload = JSON.parse(line.slice(6));
                    if (payload.done) break;
                    if (payload.token) {
                        textEl.textContent += payload.token;
                        scrollToBottom();
                    }
                } catch (e) {
                    // Malformed JSON line — skip
                }
            }
        }

    } catch (e) {
        hideTyping();
        addJarvisMessage("Sir, I'm unable to reach the backend. Is the server running?");
    }

    isStreaming = false;
}

// ── Voice Input ──────────────────────────────────────────────────

async function startVoice() {
    if (isRecording || isStreaming) return;

    isRecording = true;
    btnMic.classList.add("recording");
    btnMic.textContent = "REC";

    addJarvisMessage("Listening...");
    showTyping();

    try {
        const res = await fetch(`${API}/voice/listen`, { method: "POST" });
        const data = await res.json();

        hideTyping();

        if (data.heard) {
            addUserMessage(data.heard);
        }
        if (data.response) {
            addJarvisMessage(data.response);
        }

    } catch (e) {
        hideTyping();
        addJarvisMessage("Voice system offline. Ensure the backend is running.");
    }

    btnMic.classList.remove("recording");
    btnMic.textContent = "MIC";
    isRecording = false;
}

// ── Quick Action Buttons ─────────────────────────────────────────

async function getSystemInfo() {
    showTyping();
    try {
        const res = await fetch(`${API}/system/info`);
        const data = await res.json();
        hideTyping();
        addJarvisMessage(data.info || "System info unavailable.");
    } catch (e) {
        hideTyping();
        addJarvisMessage("Unable to fetch system info. Backend offline.");
    }
}

async function promptWebSearch() {
    const query = prompt("Enter search query:");
    if (!query) return;

    addUserMessage(`Search: ${query}`);
    showTyping();

    try {
        const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        hideTyping();
        addJarvisMessage(data.results || "No results found.");
    } catch (e) {
        hideTyping();
        addJarvisMessage("Search failed. Backend offline.");
    }
}

async function getReminders() {
    showTyping();
    try {
        const res = await fetch(`${API}/reminders`);
        const data = await res.json();
        hideTyping();
        addJarvisMessage(data.reminders || "No reminders.");
    } catch (e) {
        hideTyping();
        addJarvisMessage("Unable to fetch reminders. Backend offline.");
    }
}

function clearChat() {
    // Keep only the welcome message
    while (chatMessages.children.length > 1) {
        chatMessages.removeChild(chatMessages.lastChild);
    }
}

// ── Keyboard Shortcuts ───────────────────────────────────────────

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
    if (e.key === "Escape") {
        chatInput.value = "";
    }
});

// ── Initialise ───────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    checkStatus();
    playStartupTone();
    chatInput.focus();

    // Refresh status every 30 seconds
    setInterval(checkStatus, 30000);
});
