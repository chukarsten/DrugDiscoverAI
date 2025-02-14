import os
from prompts.prompts import intro_prompt, system_prompt # Import the prompts from prompts.py

import anthropic
import google.generativeai
import logging
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from openai import OpenAI

app = Flask(__name__)

# Configure Flask session (stores in server-side memory)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"

Session(app)

# Check if Gemini is enabled
GEMINI_ENABLED = os.getenv("GEMINI_ENABLED", "false").lower() == "true"


def get_model_response(mode, messages):
    if mode == "ChatGPT":
        openai = OpenAI()
        model = "gpt-4o-mini"
        response = openai.chat.completions.create(model=model, messages=messages)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
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
            max_tokens=200,
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


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    mode = request.json.get("mode")
    print(f"Mode: {mode}")

    print(user_message)
    # Retrieve conversation history
    history = session.get("history", [])

    # Rebuild LLM message history
    messages = []
    for message in history:
        messages.append({"role": message["user"], "content": message["message"]})
    messages.append(
        {"role": "user", "content": user_message}
    )

    # Generate bot response
    response_message = get_model_response(mode, messages)

    # Append messages to history
    history.append({"user": "user", "message": user_message})
    history.append({"user": "assistant", "message": response_message})

    # Save back to session
    session["history"] = history
    print(response_message)
    return jsonify({"reply": response_message})


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
    app.run(host="0.0.0.0", port=5000, debug=True)
