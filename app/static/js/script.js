// Switch
const toggle = document.getElementById('modeToggle');
const modeLabel = document.getElementById('modeLabel');

function sendMessage() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<div class='user'>You: ${userInput}</div>`;
    const mode = toggle.checked ? 'API' : 'Local'
    fetch("/chat", {
        method: "POST",
        body: JSON.stringify({ message: userInput, mode: mode }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => {
         if (!response.ok) {
             throw new Error(`HTTP Error: ${response.status}`);
         }
         return response.json();
    })
    .then(data => {
        chatbox.innerHTML += `<div class='assistant'>Bot: ${data.reply}</div>`;
        chatbox.scrollTop = chatbox.scrollHeight;
    })
    .catch(error => {
        console.error('Error during fetch:', error);
        chatbox.innerHTML += `<div class='assistant error'>Error: Unable to process your message.</div>`;
    });

    document.getElementById("userInput").value = "";
}

// Add event listener for "Enter" key
document.getElementById("userInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();  // Prevent form submission (if inside a form)
        sendMessage();
    }
});



toggle.addEventListener('change', () => {
  if (toggle.checked) {
    modeLabel.textContent = "Current Mode: API";
    setMode('API'); // Function to set mode to API
  } else {
    modeLabel.textContent = "Current Mode: Local";
    setMode('Local'); // Function to set mode to Local
  }
});

function setMode(mode) {
  // Send the mode to the back-end or handle front-end logic
  // Example for a fetch request to API if needed:
  if (mode === 'API') {
    fetch('/api-endpoint')
      .then(response => response.json())
      .then(data => {
        console.log(data); // Handle API response
      });
  } else {
    // Handle local mode logic
    console.log('Using Local Mode');
  }
}

function loadInitialMessage() {
    const mode = toggle.checked ? 'API' : 'Local'; // Determine the mode based on the toggle state

    fetch("/initial-message", {
        method: "POST", // Changed to POST for sending the mode
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: mode }) // Pass mode to backend
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        let chatbox = document.getElementById("chatbox");
        chatbox.innerHTML += `<div class='assistant'>Bot: ${data.reply}</div>`;
    })
    .catch(error => {
        console.error('Error during initial fetch:', error);
        let chatbox = document.getElementById("chatbox");
        chatbox.innerHTML += `<div class='assistant error'>Error: Unable to load the initial message.</div>`;
    });
}

// Load initial bot message when page loads
window.onload = loadInitialMessage;