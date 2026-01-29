import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# El cliente toma la API key desde GEMINI_API_KEY
client = genai.Client()

@app.route("/")
def home():
    return "Backend IA activo"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "Falta 'prompt'"}), 400

        prompt = data["prompt"]

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return jsonify({
            "response": response.text
        })

    except Exception as e:
        return jsonify({
            "error": "Error interno",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
