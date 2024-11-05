let sessionId = null;

const loaderHtml = `
<div id="container">
  <div id="ball-1" class="circle"></div>
  <div id="ball-2" class="circle"></div>
  <div id="ball-3" class="circle"></div>
<div>`;

// Get the current domain from the browser
const domain = window.location.origin;

// Function to toggle chat window visibility
function toggleChat() {
  const chatWindow = document.getElementById("chatWindow");
  chatWindow.classList.toggle("flex");
  chatWindow.classList.toggle("hidden");

  // Fetch a new session ID if the chat is opened for the first time
  if (!sessionId) {
    fetchNewSession();
  }
}

// Function to fetch a new session ID from FastAPI backend
async function fetchNewSession() {
  const response = await fetch(
    `${domain}/session`  // Use the dynamic domain
  );
  const data = await response.json();
  sessionId = data.session_id;
  console.log("Session ID:", sessionId);
  console.log("Data", data);
}

// Function to handle message send event
async function handleSend() {
  const chatInput = document.getElementById("chatInput");
  const userMessage = chatInput.value.trim();

  if (userMessage) {
    addMessageToChat(userMessage, "user");
    chatInput.value = "";

    const loadingMessageElement = addMessageToChat("...", "bot", true);

    // Send user message to FastAPI backend and get the bot response
    const botResponse = await sendMessageToBot(userMessage);

    loadingMessageElement.remove();

    // Display bot response
    addMessageToChat(botResponse.response, "bot");
  }
}

// Function to send user message to FastAPI backend
async function sendMessageToBot(userMessage) {
  if (!sessionId) {
    console.error("Session ID is missing");
    return { response: "Error: No session ID found." };
  }

  const response = await fetch(
    `${domain}/chat/${sessionId}`,  // Use the dynamic domain
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: userMessage }),
    }
  );
  
  let res = await response.json();
  return res;
}

// Function to add message to chat window
function addMessageToChat(message, sender, isLoading = false) {
  const chatBody = document.getElementById("chatBody");
  const messageElement = document.createElement("div");
  messageElement.className = `message ${sender}-message`;

  if (isLoading) {
    messageElement.classList.add("loading");
    messageElement.innerHTML = loaderHtml;
  } else {
    if (sender === "bot") {
      typeText(message, messageElement, 2, 50);
    } else {
      messageElement.textContent = message;
    }
  }

  chatBody.appendChild(messageElement);
  chatBody.scrollTop = chatBody.scrollHeight;

  return messageElement;
}

function typeText(text, element, charactersPerStep = 1, speed = 50) {
  console.log(text);

  let index = 0;

  function type() {
    if (index < text.length) {
      element.textContent += text.substr(index, charactersPerStep);
      index += charactersPerStep;
      setTimeout(type, speed);
    }
  }

  type();
}

// Add event listener to handle 'Enter' key press
document
  .getElementById("chatInput")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      handleSend();
    }
  });

const mobileNavBtn = document.querySelector(".mobile-nav-btn");
const mobileNav = document.querySelector(".mobile-nav");

mobileNavBtn.addEventListener("click", () => {
  mobileNav.classList.toggle("active");
});
