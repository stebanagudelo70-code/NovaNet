from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import yaml
import os
import sys
import re
import requests
import json

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from database import init_db, buscar_cliente_por_cedula, registrar_pago, registrar_reporte_falla
from tools.pagos import procesar_pago
from tools.red import simulacion
from tools.MemoriaDinamica import memoria


with open(os.path.join(BASE_DIR, "docs", "novanet_identity.yaml"), "r", encoding="utf-8") as f:
    identity = yaml.safe_load(f)

ident = identity['identity']
NOMBRE = ident['nombre']
MISION = ident['mision']
VOZ_TONO = ident['voz']['tono']

AGENTS_CONTEXT = ""
try:
    with open(os.path.join(BASE_DIR, "docs", "AGENTS.md"), "r", encoding="utf-8") as f:
        AGENTS_CONTEXT = f.read()
    print(f"[OK] AGENTS.md cargado ({len(AGENTS_CONTEXT)} caracteres)")
except FileNotFoundError:
    print("[!] AGENTS.md no encontrado - el agente funcionara sin contexto del proyecto")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_ENABLED = bool(OPENROUTER_API_KEY and OPENROUTER_API_KEY != "tu_api_key_aqui")
if LLM_ENABLED:
    print(f"[OK] LLM habilitado (OpenRouter)")
else:
    print("[!] LLM deshabilitado - configure OPENROUTER_API_KEY en .env para activar")

print(f"[OK] {NOMBRE} inicializado")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

init_db()

sesiones = {}


def _obtener_ip_cliente(cliente):
    return cliente.get('ip',
           cliente.get('ip_asignada',
           cliente.get('ip_cliente',
           cliente.get('direccion_ip',
           cliente.get('ip_address',
           cliente.get('ip_del_router', 'No asignada'))))))


def _obtener_router_cliente(cliente):
    return cliente.get('router',
           cliente.get('router_asignado',
           cliente.get('nombre_router',
           cliente.get('router_name', 'No asignado'))))


def _obtener_plan_cliente(cliente):
    return cliente.get('plan',
           cliente.get('tipo_plan',
           cliente.get('plan_nombre', 'básico')))


def llamar_llm(mensaje, sesion=None, session_id=None):
    if not LLM_ENABLED:
        return None

    contexto_cliente = ""
    if sesion and sesion.get("cliente"):
        c = sesion["cliente"]
        contexto_cliente = (
            f"\n\n## Datos del cliente actual:\n"
            f"- Nombre: {c.get('nombre', '')} {c.get('apellido', '')}\n"
            f"- Cedula: {sesion.get('cedula', '')}\n"
            f"- Plan: {_obtener_plan_cliente(c)}\n"
            f"- Router: {_obtener_router_cliente(c)}\n"
            f"- IP: {_obtener_ip_cliente(c)}\n"
        )

    estado_red = simulacion.obtener_resumen()
    contexto_red = (
        f"\n\n## Estado actual de la red:\n"
        f"- Routers operativos: {estado_red['verde']}/{estado_red['total']}\n"
        f"- Con falla menor: {estado_red['naranja']}/{estado_red['total']}\n"
        f"- Requieren tecnico: {estado_red['rojo']}/{estado_red['total']}\n"
        f"- Disponibilidad: {estado_red['disponibilidad']}\n"
    )

    system_prompt = f"""Eres {NOMBRE}, un asesor de atencion al cliente para un proveedor de internet ISP.

Tu mision: {MISION}

Tu tono: {VOZ_TONO}

## Quien eres:
Eres novaNet, el asistente digital de una empresa de internet. No eres un robot ni un formulario.
Eres como un asesor de confianza que habla por WhatsApp o Messenger. Hablas como persona real.

## Contexto del proyecto:
{AGENTS_CONTEXT}
{contexto_cliente}{contexto_red}

## Como debes conversar:

### ESTILO
- Respuestas CORTAS y DIRECTAS, como en una conversacion real de chat.
- Usa lenguaje natural. Ejemplo: "Dejame revisar eso" en vez de "Procesando solicitud..."
- Un emoji por mensaje es suficiente. No saturar.
- No uses listas numeradas a menos que sea realmente necesario (como listar planes).
- No repitas lo que ya dijiste. Si el cliente pregunta algo diferente, responde diferente.
- Si el cliente esta frustrado, reconoce su frustracion antes de ofrecer solucion.
- No cierres cada mensaje con "En que mas puedo ayudarte?" — suena robotico.

### EJEMPLOS DE COMO HABLAR

Mala respuesta (robotica):
"Ha sido verificada exitosamente su cuenta. A continuacion se muestra la informacion de su servicio: Plan: Premium, Router: Router-Alpha, IP: 192.168.1.1."

Buena respuesta (natural):
"¡Listo! Ya revise tu cuenta y todo esta bien por el lado del servicio. Tu router esta funcionando sin problemas, asi que tu conexion deberia estar estable. ¿Hay algo mas que necesites?"

Mala respuesta (robotica):
"Los planes disponibles son: 1. Plan Basico - 20 Mbps - $59,900/mes. 2. Plan Premium - 50 Mbps - $99,900/mes."

Buena respuesta (natural):
"Tenemos tres opciones: el Basico con 20 megas a $59,900, el Premium con 50 megas a $99,900 y el Business con 100 megas a $149,900. Todos incluyen instalacion gratis y soporte 24/7. ¿Cual te llama la atencion?"

### REGLAS
- Responde SIEMPRE en espanol.
- Si el cliente reporta una falla, revisa su router y ofrece solucion naturalmente.
- Si el cliente quiere pagar, ofrece los metodos de forma conversacional.
- Si pregunta por planes, explicalos como se los contarias a un amigo.
- Si no sabes algo, di la verdad en vez de inventar.
- Nunca inventes precios o datos que no esten en el contexto.
- Si el cliente no se ha identificado y necesitas su cedula, pedula de forma natural, no como un formulario.
- No uses frases como "Estimado cliente" o "Le informamos que" — suena a correo corporativo.
- No des instrucciones paso a paso cuando una frase basta.
- MANTEN CONTEXTO de lo que el cliente ya te dijo en esta conversacion. No le pidas datos que ya dio.
- Si el cliente cambio de tema, responde al tema nuevo sin preguntar por el anterior."""

    messages = [{"role": "system", "content": system_prompt}]

    if session_id:
        historial = memoria.obtener_historial(session_id)
        for turno in historial:
            messages.append({
                "role": turno["role"],
                "content": turno["content"]
            })

    messages.append({"role": "user", "content": mensaje})

    try:
        respuesta = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/auto",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7,
            },
            timeout=15,
        )

        if respuesta.status_code == 200:
            data = respuesta.json()
            contenido = data["choices"][0]["message"]["content"]
            if not contenido:
                print("[LLM] Respuesta vacia del modelo")
                return None
            print(f"[LLM] Respuesta generada ({len(contenido)} caracteres)")
            return contenido
        else:
            print(f"[LLM ERROR] Status {respuesta.status_code}: {respuesta.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print("[LLM ERROR] Timeout - respuesta del LLM tarda demasiado")
        return None
    except requests.exceptions.ConnectionError:
        print("[LLM ERROR] Error de conexion con OpenRouter")
        return None
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return None


def clasificar_intencion(mensaje):
    msg = mensaje.lower()
    patron_cedula = r'\b(\d{6,12})\b'

    if any(p in msg for p in ['falla', 'no funciona', 'caído', 'caido', 'sin internet', 'sin señal',
                               'problema', 'lento', 'interrumpido', 'no conecta', 'se cayó',
                               'soporte', 'ayuda técnica', 'reporte', 'reportar']):
        return "soporte"

    if any(p in msg for p in ['pago', 'pagar', 'factura', 'debo', 'cuota', 'abono',
                               'mercado pago', 'visa', 'tarjeta', 'cuenta']):
        return "pagos"

    if any(p in msg for p in ['plan', 'planes', 'precio', 'velocidad', 'mega', 'mbps',
                               'contratar', 'nuevo servicio', 'cambiar plan', 'qué ofrecen',
                               'que ofrecen', 'disponible', 'promocion', 'promoción']):
        return "ventas"

    if re.search(patron_cedula, msg):
        return "identificacion"

    return "general"


@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'source', 'frontend', 'chat'), 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'source', 'frontend', 'chat'), filename)


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "agent": NOMBRE,
        "version": "2.0",
        "sesiones_activas": memoria.total_sesiones_activas()
    })


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')

        if session_id not in sesiones:
            sesiones[session_id] = {
                "estado": "inicial",
                "cedula": None,
                "cliente": None,
                "intencion": None
            }

        sesion = sesiones[session_id]
        intencion = clasificar_intencion(message)
        sesion["intencion"] = intencion

        memoria.registrar_turno(session_id, "user", message)

        respuesta = procesar_mensaje(message, sesion, intencion, session_id)

        memoria.registrar_turno(session_id, "assistant", respuesta)

        return jsonify({
            "response": respuesta,
            "session_id": session_id,
            "intencion": intencion
        })

    except Exception as e:
        print(f"Error en /chat: {e}")
        return jsonify({
            "response": "Lo siento, ha ocurrido un error. Por favor, intente de nuevo."
        }), 500


def procesar_mensaje(message, sesion, intencion, session_id=None):
    if intencion == "identificacion" or sesion["estado"] == "esperando_cedula":
        return manejar_identificacion(message, sesion)

    if intencion == "soporte":
        if not sesion["cliente"]:
            sesion["estado"] = "esperando_cedula"
            return ("🔧 Hola, veo que necesitas ayuda técnica. Para revisar tu servicio, necesito verificar tu cuenta.\n\n"
                    "¿Me pasas tu cédula de cliente?")
        else:
            respuesta_llm = llamar_llm(message, sesion, session_id)
            if respuesta_llm:
                return respuesta_llm
            return manejar_soporte(message, sesion)

    if intencion == "pagos":
        if not sesion["cliente"]:
            sesion["estado"] = "esperando_cedula"
            return ("💳 ¡Hola! Para ayudarte con tu pago, necesito primero identificar tu cuenta.\n\n"
                    "¿Cuál es tu cédula de cliente?")
        else:
            if sesion["estado"] in ("procesando_pago", "seleccionando_pago"):
                return manejar_pagos(message, sesion)
            respuesta_llm = llamar_llm(message, sesion, session_id)
            if respuesta_llm:
                return respuesta_llm
            return manejar_pagos(message, sesion)

    if intencion == "ventas":
        respuesta_llm = llamar_llm(message, sesion, session_id)
        if respuesta_llm:
            return respuesta_llm
        return manejar_ventas(message, sesion)

    respuesta_llm = llamar_llm(message, sesion, session_id)
    if respuesta_llm:
        return respuesta_llm

    return ("¡Hola! Soy novaNet, tu asesor digital de internet. ¿En qué te puedo ayudar hoy?\n\n"
            "Puedo ayudarte con soporte técnico, pagos o información sobre nuestros planes.")


def manejar_identificacion(message, sesion):
    cedula_match = re.search(r'\b(\d{6,12})\b', message)
    if not cedula_match:
        return "No encontré un número de cédula válido. ¿Podrías escribirlo solo con números, por ejemplo: 1234567890?"

    cedula = cedula_match.group(1)
    cliente = buscar_cliente_por_cedula(cedula)

    if not cliente:
        return (f"No encontré una cuenta asociada a la cédula {cedula}. "
                "¿Podrías verificar el número? Si tienes dudas, puedes contactar a soporte.")

    sesion["cliente"] = cliente
    sesion["cedula"] = cedula
    sesion["estado"] = "identificado"

    nombre = cliente.get('nombre', 'Cliente')
    apellido = cliente.get('apellido', '')
    plan = _obtener_plan_cliente(cliente)
    ip = _obtener_ip_cliente(cliente)
    router = _obtener_router_cliente(cliente)

    print(f"[DEBUG] Cliente identificado: {nombre} | ip='{ip}' | router='{router}'")

    respuesta_cliente = (f"¡Hola {nombre} {apellido}! Ya verifiqué tu cuenta.\n\n"
                         f"Veo que tienes el plan **{plan}**, con router **{router}** (IP: {ip}).\n\n")

    resultado_red = simulacion.atender_cliente(ip)
    respuesta_cliente += resultado_red["mensaje"]

    if resultado_red["accion"] == "reiniciado":
        registrar_reporte_falla(cliente['id'], f"Reinicio automático por falla naranja en {router}")

    elif resultado_red["accion"] == "tecnico_despachado":
        registrar_reporte_falla(cliente['id'], f"Falla roja crítica en {router} - Técnico despachado")

    respuesta_cliente += "\n\n¿En qué más te puedo ayudar?"

    return respuesta_cliente


def manejar_soporte(message, sesion):
    cliente = sesion["cliente"]
    ip = _obtener_ip_cliente(cliente)
    router = _obtener_router_cliente(cliente)

    if sesion["estado"] == "reportando_falla":
        return procesar_reporte_falla(message, sesion)

    resultado_red = simulacion.atender_cliente(ip)

    if resultado_red["accion"] == "reiniciado":
        registrar_reporte_falla(cliente['id'], f"Reinicio automático por falla naranja en {router}")

    elif resultado_red["accion"] == "tecnico_despachado":
        registrar_reporte_falla(cliente['id'], f"Falla roja crítica en {router} - Técnico despachado")

    return resultado_red["mensaje"] + "\n\nSi necesitas reportar algo más, cuéntame lo que está pasando."


def procesar_reporte_falla(message, sesion):
    cliente = sesion["cliente"]
    reporte_id = registrar_reporte_falla(cliente['id'], message)

    return (f"Listo, ya registré tu reporte (ID: {reporte_id}). "
            f"Un técnico lo revisará pronto y te notificaremos cuando haya novedades.\n\n"
            f"¿Hay algo más en lo que te pueda ayudar?")


def manejar_pagos(message, sesion):
    msg = message.lower()

    if sesion["estado"] == "procesando_pago":
        return procesar_pago_cliente(message, sesion)

    if any(p in msg for p in ['pagar', 'pago', 'abonar', 'abono']):
        sesion["estado"] = "seleccionando_pago"
        plan = _obtener_plan_cliente(sesion['cliente'])
        return ("¿Con cuál método prefieres pagar? Tienes **Mercado Pago** (rápido y seguro) o **Visa** (crédito o débito).\n\n"
                "Solo dime cuál prefieres.")

    if sesion["estado"] == "seleccionando_pago":
        if "mercadopago" in msg or "mercado pago" in msg or "mercado" in msg:
            sesion["metodo_pago"] = "mercadopago"
            sesion["estado"] = "procesando_pago"
            plan = _obtener_plan_cliente(sesion['cliente'])
            return ("Perfecto, Mercado Pago. Para confirmar el pago, solo escribe **confirmar** y lo proceso.\n\n"
                    "Si quieres cambiar el monto, dímelo.")

        if "visa" in msg or "tarjeta" in msg:
            sesion["metodo_pago"] = "visa"
            sesion["estado"] = "procesando_pago"
            return ("Genial, Visa. Para procesar el pago, necesito los últimos 4 dígitos de tu tarjeta.\n\n"
                    "Escríbelos cuando quieras.")

        return "No entendí bien. ¿Prefieres **Mercado Pago** o **Visa**?"

    plan = _obtener_plan_cliente(sesion['cliente'])
    return (f"Tu plan actual es **{plan}**. ¿Qué necesitas hacer?\n\n"
            f"Si quieres **pagar**, solo dime. También puedes consultar tu factura o historial.")


def procesar_pago_cliente(message, sesion):
    msg = message.lower()
    cliente = sesion["cliente"]

    if sesion["metodo_pago"] == "visa" and sesion.get("esperando_tarjeta"):
        numero = re.sub(r'\D', '', message)
        if len(numero) < 4:
            return "Necesito al menos 4 dígitos. ¿Puedes escribirlos de nuevo?"

        resultado = procesar_pago("visa", 59.90, {"numero_tarjeta": numero})
        registrar_pago(cliente['id'], 59.90, "visa", resultado["referencia"])

        sesion["estado"] = "identificado"
        sesion.pop("metodo_pago", None)
        sesion.pop("esperando_tarjeta", None)

        return (f"¡Listo! Ya procesé tu pago con Visa. {resultado['mensaje']}\n\n"
                f"Gracias por tu pago. ¿Hay algo más en lo que te pueda ayudar?")

    if "confirmar" in msg or "confirmo" in msg:
        if sesion["metodo_pago"] == "mercadopago":
            resultado = procesar_pago("mercadopago", 59.90)
            registrar_pago(cliente['id'], 59.90, "mercadopago", resultado["referencia"])

            sesion["estado"] = "identificado"
            sesion.pop("metodo_pago", None)

            return (f"¡Perfecto! Ya confirmé tu pago con Mercado Pago. {resultado['mensaje']}\n\n"
                    f"Gracias por tu pago. ¿Necesitas algo más?")

    if sesion["metodo_pago"] == "visa":
        sesion["esperando_tarjeta"] = True
        return "¿Cuáles son los últimos 4 dígitos de tu tarjeta Visa?"

    return "No pude procesar el pago. ¿Podrías intentar de nuevo?"


def manejar_ventas(message, sesion):
    msg = message.lower()

    if any(p in msg for p in ['plan', 'planes', 'velocidad', 'mega', 'mbps', 'oferta']):
        return mostrar_planes()

    if any(p in msg for p in ['contratar', 'nuevo', 'cambiar', 'upgrade', 'actualizar']):
        return ("¡Qué bueno que te interesa! Te cuento nuestras opciones:\n\n"
                f"{mostrar_planes()}\n\n"
                "¿Cuál te llama la atención?")

    return mostrar_planes()


def mostrar_planes():
    return ("Tenemos tres planes:\n\n"
            "🟢 **Básico** — 20 megas a $59,900/mes. Ideal para navegar y redes sociales.\n"
            "🔵 **Premium** — 50 megas a $99,900/mes. Perfecto para streaming y gaming.\n"
            "🟣 **Business** — 100 megas a $149,900/mes. Para empresas y oficinas.\n\n"
            "Todos incluyen instalación gratis, router WiFi y soporte 24/7.\n\n"
            "¿Cuál te gustaría conocer con más detalle?")


@app.route('/planes')
def obtener_planes():
    planes = [
        {
            "id": 1, "nombre": "Básico", "velocidad": "20 Mbps",
            "precio": 59900, "descripcion": "Ideal para navegación básica",
            "color": "#10b981"
        },
        {
            "id": 2, "nombre": "Premium", "velocidad": "50 Mbps",
            "precio": 99900, "descripcion": "Ideal para streaming y gaming",
            "color": "#3b82f6"
        },
        {
            "id": 3, "nombre": "Business", "velocidad": "100 Mbps",
            "precio": 149900, "descripcion": "Ideal para empresas y oficinas",
            "color": "#8b5cf6"
        }
    ]
    return jsonify({"planes": planes})


@app.route('/estado-red')
def estado_red():
    routers = simulacion.obtener_todos_routers()
    return jsonify({"routers": routers})


@app.route('/cliente/<cedula>')
def obtener_cliente(cedula):
    cliente = buscar_cliente_por_cedula(cedula)
    if cliente:
        return jsonify({"cliente": cliente})
    return jsonify({"error": "Cliente no encontrado"}), 404


@app.route('/simulacion')
def simulacion_red():
    return send_from_directory(os.path.join(BASE_DIR, 'source', 'frontend', 'simulator'), 'index.html')


@app.route('/simulacion/<path:filename>')
def simulacion_archivos(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'source', 'frontend', 'simulator'), filename)


def on_router_state_change(router_data, old_state, new_state, reason):
    event = {
        "ip": router_data["ip"],
        "nombre": router_data["nombre"],
        "estado_anterior": old_state,
        "estado_nuevo": new_state,
        "razon": reason,
        "router": router_data
    }
    socketio.emit('estado_actualizado', event)
    print(f"[WS BROADCAST] {router_data['nombre']}: {old_state} -> {new_state} ({reason})")


simulacion.on_state_change(on_router_state_change)


@socketio.on('cambiar_estado')
def handle_cambiar_estado(data):
    ip = data.get('ip', '')
    nuevo_estado = data.get('nuevo_estado', '')
    reason = data.get('reason', 'Cambio desde simulador')

    print(f"[WS] Cambio solicitado: {ip} -> {nuevo_estado}")

    if nuevo_estado == 'verde':
        result = simulacion.reiniciar_router(ip)
        if result:
            emit('estado_cambiado', {"success": True, "router": result["router"]})
        else:
            emit('estado_cambiado', {"success": False, "mensaje": "Router no encontrado"})
    else:
        router = simulacion.cambiar_estado(ip, nuevo_estado, reason)
        if router:
            emit('estado_cambiado', {"success": True, "router": router})
        else:
            emit('estado_cambiado', {"success": False, "mensaje": "Router no encontrado"})


@socketio.on('solicitar_estado')
def handle_solicitar_estado():
    routers = simulacion.obtener_todos_routers()
    emit('estado_completo', {"routers": routers})


@socketio.on('simular_falla')
def handle_simular_falla(data=None):
    router = simulacion.simular_falla_aleatoria()
    if router:
        emit('falla_simulada', {"router": router})
    else:
        emit('falla_simulada', {"error": "No hay routers disponibles para falla"})


@socketio.on('conectar_simulador')
def handle_conectar_simulador(data=None):
    routers = simulacion.obtener_todos_routers()
    emit('estado_completo', {"routers": routers})
    print(f"[WS] Simulador conectado - {len(routers)} routers enviados")


if __name__ == '__main__':
    resumen = simulacion.obtener_resumen()

    print("\n" + "="*60)
    print(f">> {NOMBRE} - Agente de Soporte, Pagos y Ventas")
    print("="*60)
    print(f"Mision: {MISION}")
    print(f"Tono: {VOZ_TONO}")
    print(f"Servidor: http://localhost:5000")
    print(f"WebSocket: Habilitado (flask-socketio)")
    print(f"Estado de la red:")
    print(f"   Operativos: {resumen['verde']}/{resumen['total']}")
    print(f"   Con falla: {resumen['naranja']}/{resumen['total']}")
    print(f"   Requieren tecnico: {resumen['rojo']}/{resumen['total']}")
    print(f"   Disponibilidad: {resumen['disponibilidad']}")
    print("="*60 + "\n")

    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
