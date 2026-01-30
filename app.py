import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Cliente Gemini (usa GEMINI_API_KEY desde Railway)
client = genai.Client()

# Variables de Supabase (desde Railway)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")


def obtener_info_servicios():
    """
    Consulta Supabase y obtiene la información vigente
    de Servicios Escolares.
    """
    url = f"{SUPABASE_URL}/rest/v1/servicios_escolares_info"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }
    params = {
        "select": "fechas_escolares,costos,becas",
        "order": "updated_at.desc",
        "limit": 1
    }

    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()
    return data[0] if data else {}


@app.route("/")
def home():
    return "Backend IA activo"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "Falta 'prompt'"}), 400

        user_prompt = data["prompt"]

        # 1️⃣ Obtener datos oficiales desde Supabase
        info = obtener_info_servicios()

        # 2️⃣ Construir contexto institucional
        contexto = f"""
Eres el área de Servicios Escolares.

Información oficial vigente:

FECHAS:
{info.get("fechas_escolares", "No disponible")}

COSTOS:
{info.get("costos", "No disponible")}

BECAS:
{info.get("becas", "No disponible")}
"""

        prompt_final = f"""
{contexto}

Consulta del usuario:
"{user_prompt}"

Responde de forma formal, clara y amable.
"""

        # 3️⃣ Llamar a Gemini
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt_final
        )

        return jsonify({
            "response": response.text
        })

    except Exception as e:
        return jsonify({
            "error": "Error interno",
            "details": str(e)
        }), 500



@app.route("/info", methods=["GET"])
def info_servicios():
    try:
        info = obtener_info_servicios()
        return jsonify(info)
    except Exception as e:
        return jsonify({
            "error": "Error al obtener información",
            "details": str(e)
        }), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
