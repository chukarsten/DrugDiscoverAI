import os
from dotenv import load_dotenv
from prompts.prompts import intro_prompt, system_prompt  # Import the prompts from prompts.py

import anthropic
import google.generativeai
import json

from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from flask_socketio import SocketIO, emit
from openai import OpenAI

from tools.chemistry.chemistry import tools, validate_molecule, analyze_molecule

app = Flask(__name__)

load_dotenv()

# Configure Flask session (stores in server-side memory)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"

Session(app)
socketio = SocketIO(app)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Check if Gemini is enabled
GEMINI_ENABLED = os.getenv("GEMINI_ENABLED", "false").lower() == "true"


def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    print(f"Calling tool {tool_name}")
    arguments = json.loads(tool_call.function.arguments)
    if tool_name == "validate_molecule":
        smiles = arguments.get('smiles')
        mol = validate_molecule(smiles)
        response = {
            "role": "tool",
            "content": json.dumps({"smiles": smiles, "mol": mol}),
            "tool_call_id": tool_call.id
        }
    elif tool_name == "analyze_molecule":
        smiles = arguments.get('smiles')
        analysis_results = analyze_molecule(smiles)
        response = {
            "role": "tool",
            "content": json.dumps({"smiles": smiles, "analysis_results": analysis_results}),
            "tool_call_id": tool_call.id
        }
    return response


def get_model_response(mode, messages):
    if mode == "ChatGPT":
        openai = OpenAI()
        model = "gpt-4o-mini"
        response = openai.chat.completions.create(model=model, messages=messages, tools=tools)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Handle Tool Calls
        if response.choices[0].finish_reason == "tool_calls":
            print("Calling tool!")
            message = response.choices[0].message
            response = handle_tool_call(message)
            messages.append(message)
            messages.append(response)
            response = openai.chat.completions.create(model=model, messages=messages)
        response_message = response.choices[0].message.content

    elif mode == "Local":
        openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        model = "llama3.2:1b"
        response = openai.chat.completions.create(model=model, messages=messages)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        response_message = response.choices[0].message.content
    elif mode == "Gemini" and GEMINI_ENABLED:
        model = 'gemini-2.0-flash-exp'
        gemini = google.generativeai.GenerativeModel(
            model_name=model,
            system_instruction=messages[0]["content"]
        )
        response = gemini.generate_content(messages[1:])
    elif mode == "Claude":
        model = "claude-3-5-sonnet-latest"
        claude = anthropic.Anthropic()
        response = claude.messages.create(
            model=model,
            max_tokens=500,
            temperature=0.7,
            system=messages[0]["content"],
            messages=messages[1:],
        )
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        response_message = response.content[0].text

    print(f"Model: {model}, Prompt Tokens: {input_tokens}, Completion Tokens: {output_tokens}")
    return response_message


@app.route("/")
def index():
    if "history" not in session:
        session["history"] = [{"user": "bot", "message": initial_message()}]
    print("test")
    return render_template("index.html", gemini_enabled=GEMINI_ENABLED)


@app.route('/api-endpoint', methods=['GET'])
def api_mode():
    if request.args.get('mode') == 'ChatGPT':
        return jsonify({"message": "You are using ChatGPT mode!"})
    if request.args.get('mode') == 'Gemini':
        return jsonify({"message": "You are using Gemini mode!"})
    if request.args.get('mode') == 'Claude':
        return jsonify({"message": "You are using Claude mode!"})
    else:
        return jsonify({"message": "You are using Local mode!"})


@socketio.on('message')
def handle_message(data):
    user_message = data.get("message")
    mode = data.get("mode")
    print(f"Socket IO Mode: {mode}")
    print(user_message)

    # Retrieve conversation history
    history = session.get("history", [])

    # Rebuild LLM message history
    messages = [{"role": message["user"], "content": message["message"]} for message in history]
    messages.append({"role": "user", "content": user_message})

    # Generate bot response
    response_message = get_model_response(mode, messages)

    # Append messages to history
    history.append({"user": "user", "message": user_message})
    history.append({"user": "assistant", "message": response_message})

    # Save back to session
    session["history"] = history
    print(response_message)
    emit('response', {'reply': response_message})

@socketio.on('audio')
def handle_audio(data):
    # Process the audio data received from the client
    print("Audio data received")
    # You can add your processing logic here
    # For example, save the audio data to a file or perform speech recognition

@app.route("/conversation-history", methods=["GET"])
def conversation_history():
    """Returns the full conversation history"""
    return jsonify(session.get("history", []))


@app.route("/initial-message", methods=["POST"])
def initial_message():
    # Parse the mode from the incoming request body
    if not request.is_json:  # Ensures the request has JSON content
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    mode = data.get("mode", "Local")  # Default to "Local" if mode is not provided
    print(f"Operating in {mode}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": intro_prompt}
    ]
    # Generate bot response
    response = get_model_response(mode, messages)
    print(
        f"Model: {mode}")  # , Prompt Tokens: {response.usage.prompt_tokens}, Completion Tokens: {response.usage.completion_tokens}")

    session["history"] = [{"user": "system", "message": system_prompt},
                          {"user": "user", "message": intro_prompt},
                          {"user": "assistant", "message": response}]
    return jsonify({"reply": response})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
