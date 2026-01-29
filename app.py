import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend IA activo"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    prompt = data.get("prompt", "")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "No API key"}), 500

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        },
        timeout=30
    )

    return jsonify(response.json())


# 🔴 ESTO ES LO QUE TE FALTABA
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
