import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Cargar la clave de entorno
api_key = os.getenv("GEMINI_API_KEY")

# Configurar el cliente de Gemini
genai.configure(api_key=api_key)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Falta prompt"}), 400

    try:
        # Llamada a Gemini
        response = genai.generate_text(
            model="gemini-2.5-flash",
            prompt=prompt,
            max_output_tokens=200
        )
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
