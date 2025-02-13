// Constants
const API_MODE = 'API';
const LOCAL_MODE = 'Local';
const CLASS_USER = 'user';
const CLASS_ASSISTANT = 'assistant';
const CLASS_ERROR = 'error';

// DOM elements
const toggle = document.getElementById('modeToggle');
const modeLabel = document.getElementById('modeLabel');
const userInput = document.getElementById("userInput");
const chatbox = document.getElementById("chatbox");

// Helper functions
function appendMessage(content, senderClass) {
    chatbox.innerHTML += `<div class='${senderClass}'>${content}</div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
}

function handleFetchError(chatbox, errorMessage) {
    console.error(errorMessage);
    appendMessage(`Error: ${errorMessage}`, `${CLASS_ASSISTANT} ${CLASS_ERROR}`);
}

function determineMode() {
    return toggle.checked ? API_MODE : LOCAL_MODE;
}

// Main functionality
function sendMessage() {
    const userInputValue = userInput.value.trim();
    if (!userInputValue) return;

    appendMessage(`You: ${userInputValue}`, CLASS_USER);

    const mode = determineMode();
    fetch("/chat", {
        method: "POST",
        body: JSON.stringify({ message: userInputValue, mode }),
        headers: { "Content-Type": "application/json" }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            appendMessage(`Bot: ${data.reply}`, CLASS_ASSISTANT);
        })
        .catch(error => {
            handleFetchError(chatbox, 'Unable to process your message.');
        });

    userInput.value = "";
}

function loadInitialMessage() {
    const mode = determineMode();
    fetch("/initial-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            appendMessage(`Bot: ${data.reply}`, CLASS_ASSISTANT);
        })
        .catch(error => {
            handleFetchError(chatbox, 'Unable to load the initial message.');
        });
}

function updateModeLabel(mode) {
    modeLabel.textContent = `Current Mode: ${mode}`;
}

function handleToggleChange() {
    const mode = determineMode();
    updateModeLabel(mode);
    setMode(mode);
}

function setMode(mode) {
    if (mode === API_MODE) {
        fetch('/api-endpoint')
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Failed to fetch API data:', error));
    } else {
        console.log('Using Local Mode');
    }
}

// Event listeners
userInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

toggle.addEventListener('change', handleToggleChange);
window.onload = loadInitialMessage;