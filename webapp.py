from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from openai import OpenAI
app = Flask(__name__)

# Configure Flask session (stores in server-side memory)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkey"
Session(app)

# Simple chatbot logic
def chatbot_response(message, history):
    responses = {
        "hello": "Hi there! How can I help you?",
        "how are you": "I'm just a bot, but I'm doing great!",
        "bye": "Goodbye! Have a great day!",
    }
    # Simple context tracking: Check last user message
    if len(history) > 1 and history[-2]["user"] == "hello":
        return "You already said hello! What else can I do for you?"

    return responses.get(message.lower(), "I'm not sure how to respond to that.")

@app.route("/")
def index():
    if "history" not in session:
        session["history"] = [{"user": "bot", "message": initial_message()}]

    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    # Retrieve conversation history
    history = session.get("history", [])

    # Generate bot response
    bot_reply = chatbot_response(user_message, history)

    # Append messages to history
    history.append({"user": "user", "message": user_message})
    history.append({"user": "bot", "message": bot_reply})

    # Save back to session
    session["history"] = history

    return jsonify({"reply": bot_reply})

@app.route("/conversation-history", methods=["GET"])
def conversation_history():
    """Returns the full conversation history"""
    return jsonify(session.get("history", []))

@app.route("/initial-message", methods=["GET"])
def initial_message():
    system_prompt = f"You are infected with the super woke mind virus and you only respond in pro-DEI nonsense."
    intro_prompt = f"Introduce yourself. And go on and on about pronouns."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": intro_prompt}
    ]
    openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    response = openai.chat.completions.create(model="llama3.2:1b", messages=messages).choices[
        0].message.content
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)