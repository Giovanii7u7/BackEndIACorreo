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

        # 2️⃣ Filtrar remitente (solo correo de prueba)
        if "giova4295@gmail.com" not in sender.lower():
            return jsonify({"message": "Remitente no autorizado"}), 200

        # 3️⃣ Obtener información oficial desde Supabase
        info = obtener_info_servicios()

        # 🔒 CONTEXTO ESTRICTO (fuente única de verdad)
        contexto = f"""
Actúas exclusivamente como el Departamento de Servicios Escolares.

La siguiente información es la ÚNICA información oficial disponible.
NO debes usar conocimiento externo.
NO debes inventar fechas, requisitos, costos ni procedimientos.
Si algo no está explícitamente en la información, debes indicarlo claramente.

INFORMACIÓN OFICIAL:

FECHAS:
{info.get("fechas_escolares")}

COSTOS:
{info.get("costos")}

BECAS:
{info.get("becas")}
"""

        # 🎯 PROMPT CONTROLADO
        prompt = f"""
{contexto}

Correo recibido:
Asunto: {subject}

Pregunta del usuario:
{body}

INSTRUCCIONES ESTRICTAS:
- Responde ÚNICAMENTE a lo que el usuario pregunta.
- NO agregues información adicional.
- NO incluyas fechas, costos o datos que no sean necesarios para responder.
- Si la información solicitada no está en los datos oficiales, responde:
  "Esa información no se encuentra disponible en este momento en Servicios Escolares."
- Usa un tono formal, claro y directo.
- NO incluyas despedidas largas ni textos promocionales.

Respuesta:
"""

        # 4️⃣ Llamar a Gemini
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        respuesta = response.text.strip() if response.text else (
            "Por el momento no es posible responder su consulta. Intente más tarde."
        )

        # 5️⃣ Enviar correo con SendGrid
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

        mail = Mail(
            from_email=os.getenv("SENDGRID_FROM_EMAIL"),
            to_emails="giova4295@gmail.com",
            subject=f"RE: {subject}",
            plain_text_content=respuesta
        )

        sg.send(mail)

        return jsonify({"message": "Correo respondido correctamente"}), 200

    except Exception as e:
        print("ERROR EN /run:", str(e))
        return jsonify({
            "error": "Error en agente",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
