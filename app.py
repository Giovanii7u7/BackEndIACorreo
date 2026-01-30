import os
import requests
from flask import Flask, request, jsonify
from google import genai
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


app = Flask(__name__)
CORS(app)

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


def obtener_estado_agente():
    url = f"{SUPABASE_URL}/rest/v1/config_agente"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }
    params = {
        "select": "activo",
        "order": "updated_at.desc",
        "limit": 1
    }

    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()
    return data[0]["activo"] if data else False





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


@app.route("/info", methods=["PUT"])
def actualizar_info_servicios():
    try:
        data = request.get_json()

        fechas = data.get("fechas_escolares")
        costos = data.get("costos")
        becas = data.get("becas")

        if not fechas or not costos or not becas:
            return jsonify({"error": "Datos incompletos"}), 400

        url = f"{SUPABASE_URL}/rest/v1/servicios_escolares_info"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        payload = {
            "fechas_escolares": fechas,
            "costos": costos,
            "becas": becas
        }

        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()

        return jsonify({"message": "Información actualizada correctamente"})

    except Exception as e:
        return jsonify({
            "error": "Error al actualizar información",
            "details": str(e)
        }), 500



@app.route("/config/agente", methods=["GET"])
def obtener_config_agente():
    try:
        activo = obtener_estado_agente()
        return jsonify({"activo": activo})
    except Exception as e:
        return jsonify({
            "error": "Error al obtener estado del agente",
            "details": str(e)
        }), 500




@app.route("/config/agente", methods=["PUT"])
def actualizar_config_agente():
    try:
        data = request.get_json()
        activo = data.get("activo")

        if activo is None:
            return jsonify({"error": "Falta campo 'activo'"}), 400

        url = f"{SUPABASE_URL}/rest/v1/config_agente"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        payload = {
            "activo": bool(activo)
        }

        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()

        return jsonify({"message": "Estado del agente actualizado"})

    except Exception as e:
        return jsonify({
            "error": "Error al actualizar estado del agente",
            "details": str(e)
        }), 500


@app.route("/run", methods=["POST"])
def run_agente():
    try:
        # 1️⃣ Verificar agente activo
        if not obtener_estado_agente():
            return jsonify({"message": "Agente desactivado"}), 200

        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON inválido"}), 400

        sender = data.get("from", "")
        subject = data.get("subject", "")
        body = data.get("body", "")

        # 2️⃣ Filtrar remitente (SOLO tu correo de prueba)
        if "giovanni.20032026@outlook.com" not in sender.lower():
            return jsonify({"message": "Remitente no autorizado"}), 200

        # 3️⃣ Obtener info oficial
        info = obtener_info_servicios()

        contexto = f"""
Eres el área de Servicios Escolares.

Información oficial vigente:

FECHAS:
{info.get("fechas_escolares")}

COSTOS:
{info.get("costos")}

BECAS:
{info.get("becas")}
"""

        prompt = f"""
{contexto}

Correo recibido:
Asunto: {subject}

Contenido:
{body}

Redacta una respuesta formal y clara como Servicios Escolares.
"""

        # 4️⃣ Gemini
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        respuesta = response.text

        # 5️⃣ Enviar correo con SendGrid
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

        mail = Mail(
            from_email=os.getenv("SENDGRID_FROM_EMAIL"),
            to_emails="giovanni.20032026@outlook.com",
            subject=f"RE: {subject}",
            plain_text_content=respuesta
        )

        sg.send(mail)

        return jsonify({"message": "Correo respondido correctamente"}), 200

    except Exception as e:
        return jsonify({
            "error": "Error en agente",
            "details": str(e)
        }), 500





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
