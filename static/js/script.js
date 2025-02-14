// Constants
const API_MODE = 'API';
const LOCAL_MODE = 'Local';
const CLASS_USER = 'user';
const CLASS_ASSISTANT = 'assistant';
const CLASS_ERROR = 'error';

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const dropdown = document.getElementById('modeDropdown');
    const modeLabel = document.getElementById('modeLabel');
    const userInput = document.getElementById("userInput");
    const chatbox = document.getElementById("chatbox");
    var md = window.markdownit();  // Create a markdown-it instance


    // Helper functions
    function appendMessage(content, senderClass) {
        const htmlContent = DOMPurify.sanitize(md.render(content)); // Sanitize and convert markdown to HTML
        chatbox.innerHTML += `<div class='${senderClass}'>${htmlContent}</div>`;
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    function handleFetchError(chatbox, errorMessage) {
        console.error(errorMessage);
        appendMessage(`Error: ${errorMessage}`, `${CLASS_ASSISTANT} ${CLASS_ERROR}`);
    }

    function determineMode() {
        return dropdown.value
    }

    // Main functionality
    function sendMessage() {
        const userInputValue = userInput.value.trim();
        if (!userInputValue) return;

        appendMessage(`${userInputValue}`, CLASS_USER);

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
                appendMessage(`${data.reply}`, CLASS_ASSISTANT);
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
                appendMessage(`${data.reply}`, CLASS_ASSISTANT);
            })
            .catch(error => {
                handleFetchError(chatbox, 'Unable to load the initial message.');
            });
    }

    function updateModeLabel(mode) {
        dropdown.value = `${mode}`;
    }

    function handleDropdownChange() {
        const mode = determineMode();
        updateModeLabel(mode);
        setMode(mode);
    }

    function setMode(mode) {
        if (mode === 'ChatGPT' || mode === 'Gemini' || mode === 'Claude') {
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

    dropdown.addEventListener('change', handleDropdownChange);
    window.onload = loadInitialMessage;
});