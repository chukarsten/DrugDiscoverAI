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

    // Initialize Socket.IO
    const peerConnection = new RTCPeerConnection();
    const socket = io();

    let mediaRecorder;
    let audioChunks = [];
    let recognition;

    // Handle voice button click
    const voiceButton = document.getElementById('voiceButton');
    voiceButton.addEventListener('click', startRecording);

    function startRecording() {
        navigator.mediaDevices.getUserMedia({audio: true})
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                console.log("MediaRecorder started");

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    if (audioChunks.length > 0) {
                        const audioBlob = new Blob(audioChunks, {type: 'audio/wav'});
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
                };

                startSpeechRecognition();
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
            });
    }

    function startSpeechRecognition() {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onend = () => {
            console.log("User stopped talking.")
            mediaRecorder.stop();
        };

        recognition.start();
        console.log("Speech Recognition Started.")
    }

    socket.on('transcription', function (data) {
        appendMessage(data.transcription, CLASS_ASSISTANT);
    });

    // Helper functions
    function appendMessage(content, senderClass) {
        const htmlContent = DOMPurify.sanitize(md.render(content)); // Sanitize and convert markdown to HTML
        chatbox.innerHTML += `<div class='${senderClass}'>${htmlContent}</div>`;
        chatbox.scrollTop = chatbox.scrollHeight;
        scrollToBottom();
    }

    function scrollToBottom() {
        console.log("Scrolling to bottom");
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
    window.sendMessage = function () {
        const userInputValue = userInput.value.trim();
        if (!userInputValue) return;

        appendMessage(`${userInputValue}`, CLASS_USER);

        const mode = determineMode();
        socket.emit('message', {message: userInputValue, mode});

        userInput.value = "";
    }

    // Listen for the response event from the server
    socket.on('response', function (data) {
        const responseMessage = data.reply;
        appendMessage(responseMessage, CLASS_ASSISTANT);
    });

    function loadInitialMessage() {
        const mode = determineMode();
        fetch("/initial-message", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({mode})
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