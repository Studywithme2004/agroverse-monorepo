const chatButton = document.getElementById("ai-chat-button");
const chatPanel = document.getElementById("ai-chat-panel");
const chatClose = document.getElementById("ai-chat-close");
const chatInput = document.getElementById("ai-chat-input");
const chatSend = document.getElementById("ai-chat-send");
const chatMessages = document.getElementById("ai-chat-messages");

let chatHistory = [];

// Open panel
chatButton.addEventListener("click", () => {
  chatPanel.style.display = "flex";
});

// Close panel
chatClose.addEventListener("click", () => {
  chatPanel.style.display = "none";
});

// Send message
chatSend.addEventListener("click", sendMessage);
chatInput.addEventListener("keypress", function(e){
  if(e.key === 'Enter') sendMessage();
});

function appendMessage(sender, text) {
  const msgDiv = document.createElement("div");
  msgDiv.textContent = `${sender}: ${text}`;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;
  appendMessage("You", message);
  chatInput.value = "";

  // Add to history
  chatHistory.push({ user: message, bot: "" });

  try {
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, history: chatHistory })
    });
    const data = await response.json();
    const reply = data.reply || "AI did not respond.";
    appendMessage("Agro AI", reply);

    // Update last history entry
    chatHistory[chatHistory.length - 1].bot = reply;

  } catch (err) {
    appendMessage("Agro AI", "Error connecting to AI backend.");
    console.error(err);
  }
}
