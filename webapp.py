import logging
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from openai import OpenAI
app = Flask(__name__)

# Configure Flask session (stores in server-side memory)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"
Session(app)

@app.route("/")
def index():
    if "history" not in session:
        session["history"] = [{"user": "bot", "message": initial_message()}]

    return render_template("index.html")

@app.route('/api-endpoint', methods=['GET'])
def api_mode():
    print(request.args)
    if request.args.get('mode') == 'API':
        return jsonify({"message": "You are using API mode!"})
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
    if mode == "API":
        openai = OpenAI()
        model = "gpt-4o-mini"
    elif mode == "Local":
        openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        model = "llama3.2:1b"
    response = openai.chat.completions.create(model=model, messages=messages)
    response_message = response.choices[0].message.content
    print(
        f"Model: {response.model}, Prompt Tokens: {response.usage.prompt_tokens}, Completion Tokens: {response.usage.completion_tokens}")

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

@app.route("/initial-message", methods=["GET"])
def initial_message():
    system_prompt = f"You are Donald Trump.  Speak with an outrageous Donald Trump accent and use all of his mannerisms.\
      Frequently display actions indicating Donald Trump physical mannerisms. Constantly talk about China and bring all \
      conversations back to slamming Trump's political rivals. "
    intro_prompt = f"Introduce yourself. Don't respond in huge blocks of text.  Use paragraphs to make it readable."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": intro_prompt}
    ]
    openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    response = openai.chat.completions.create(model="llama3.2:1b", messages=messages)
    response_message = response.choices[0].message.content
    print(f"Model: {response.model}, Prompt Tokens: {response.usage.prompt_tokens}, Completion Tokens: {response.usage.completion_tokens}")

    session["history"] = [{"user": "system", "message": system_prompt},
                          {"user": "user", "message": intro_prompt},
                          {"user": "assistant", "message": response_message}]
    return jsonify({"reply": response_message})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)