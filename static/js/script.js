// Constants
const API_MODE = 'API';
const LOCAL_MODE = 'Local';
const CLASS_USER = 'user';
const CLASS_ASSISTANT = 'assistant';
const CLASS_ERROR = 'error';

// DOM elements
const dropdown = document.getElementById('modeDropdown');
const modeLabel = document.getElementById('modeLabel');
const userInput = document.getElementById("userInput");
const chatbox = document.getElementById("chatbox");
const voiceButton = document.getElementById('voiceButton');
var md = window.markdownit();  // Create a markdown-it instance

// Initialize Socket.IO
const socket = io();

// Variables for media recording and speech recognition
let mediaRecorder;
let audioChunks = [];
let recognition;

// Event Listeners
document.addEventListener('DOMContentLoaded', initialize);
voiceButton.addEventListener('click', startRecording);
userInput.addEventListener("keypress", handleKeyPress);
dropdown.addEventListener('change', handleDropdownChange);
window.onload = loadInitialMessage;

// Initialize the application
function initialize() {
    console.log("Application initialized");
}

// Start recording audio
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            console.log("MediaRecorder started");

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = handleMediaRecorderStop;

            startSpeechRecognition();
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
        });
}

// Handle MediaRecorder stop event
function handleMediaRecorderStop() {
    if (audioChunks.length > 0) {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsArrayBuffer(audioBlob);
        reader.onloadend = () => {
            const audioArrayBuffer = reader.result;
            socket.emit('audio', audioArrayBuffer);
            console.log("Audio data sent to server");
        };
        audioChunks = [];
    } else {
        console.log("No audio data available");
    }
}

// Start speech recognition
function startSpeechRecognition() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onend = () => {
        console.log("User stopped talking.");
        mediaRecorder.stop();
    };

    recognition.start();
    console.log("Speech Recognition Started.");
}

// Handle key press event in user input
function handleKeyPress(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}

// Send message to the server
function sendMessage() {
    const userInputValue = userInput.value.trim();
    if (!userInputValue) return;

    appendMessage(userInputValue, CLASS_USER);

    const mode = determineMode();
    socket.emit('message', { message: userInputValue, mode });

    userInput.value = "";
}

// Append message to the chatbox
function appendMessage(content, senderClass) {
    const htmlContent = DOMPurify.sanitize(md.render(content)); // Sanitize and convert markdown to HTML
    chatbox.innerHTML += `<div class='${senderClass}'>${htmlContent}</div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
    scrollToBottom();
}

// Scroll chatbox to the bottom
function scrollToBottom() {
    console.log("Scrolling to bottom");
    chatbox.scrollTop = chatbox.scrollHeight;
}

// Handle fetch error
function handleFetchError(chatbox, errorMessage) {
    console.error(errorMessage);
    appendMessage(`Error: ${errorMessage}`, `${CLASS_ASSISTANT} ${CLASS_ERROR}`);
}

// Determine the current mode from the dropdown
function determineMode() {
    return dropdown.value;
}

// Load the initial message
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
            appendMessage(data.reply, CLASS_ASSISTANT);
        })
        .catch(error => {
            handleFetchError(chatbox, 'Unable to load the initial message.');
        });
}

// Update the mode label
function updateModeLabel(mode) {
    dropdown.value = mode;
}

// Handle dropdown change event
function handleDropdownChange() {
    const mode = determineMode();
    updateModeLabel(mode);
    setMode(mode);
}

// Set the mode and fetch API data if necessary
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

// Listen for the response event from the server
socket.on('response', function (data) {
    const responseMessage = data.reply;
    appendMessage(responseMessage, CLASS_ASSISTANT);
});

// Listen for the transcription event from the server
socket.on('transcription', function (data) {
    appendMessage(data.transcription, CLASS_ASSISTANT);
});