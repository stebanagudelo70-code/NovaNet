


## Flujo del agente de chat

1. El cliente envía un mensaje al endpoint /chat.
2. El servidor clasifica la intención (soporte, pagos, ventas, identificación, general).
3. Si el cliente aún no se ha identificado y la intención lo requiere, se le pide la cédula de forma natural.
4. Al recibir la cédula, se busca el cliente en la BD y se verifica su cuenta.
5. Se consulta el estado del router asignado al cliente en la simulación de red.
6. Según el estado del router se ejecuta una acción: verde (todo OK), naranja (reinicio automático) o rojo (despacho de técnico).
7. Se responde al cliente con el diagnóstico de forma conversacional.

## Flujo de sincronización WebSocket

- El simulador de red se conecta al backend vía Socket.IO al iniciar sesión.
- Al conectar, el backend envía el estado completo de todos los routers.
- Cuando el técnico cambia el estado de un router en el simulador, el cambio se envía al backend.
- Cuando el agente cambia un estado (por ejemplo, reinicio automático por falla naranja), el cambio se envía a todos los simuladores conectados.
- Esto garantiza que el agente y el simulador siempre muestren el mismo estado.

## Base de datos PostgreSQL

Tabla clientes con columnas: id, nombre, apellido, cedula, router, ip, tipo_plan.

La conexión se intenta al iniciar el servidor. Si PostgreSQL no está disponible, se usan datos mock de tres clientes de prueba (cédulas 10101010, 20202020, 30303030).

## Estados de los routers

- Verde: router funcionando correctamente, cliente tiene conexión.
- Naranja: falla menor, el agente realiza un reinicio automático del router y notifica al cliente.
- Rojo: falla crítica, el agente despacha un técnico con fecha estimada de 3 días y registra el reporte.

## Planes de internet

- Básico: 20 Mbps, $59,900/mes. Ideal para navegación básica y redes sociales.
- Premium: 50 Mbps, $99,900/mes. Ideal para streaming, gaming y teletrabajo.
- Business: 100 Mbps, $149,900/mes. Ideal para empresas y oficinas con múltiples dispositivos.

Todos incluyen instalación gratuita, router WiFi y soporte técnico 24/7.

## Estilo de conversación

El agente debe sonar como un asesor humano, no como un bot genérico. Estas son las directrices:

### Cómo hablar

- Respuestas cortas y directas, como en una conversación real de WhatsApp o Messenger.
- Usa un lenguaje natural y conversacional. Ejemplo: "Déjame revisar eso" en vez de "Procesando solicitud...".
- Sé empático cuando el cliente tiene un problema: "Lamento que tengas ese problema, vamos a ver qué podemos hacer."
- Sé entusiasta cuando hay buenas noticias: "¡Buenas noticias! Tu router está funcionando perfecto."
- No uses listas numeradas o viñetas a menos que sea realmente necesario (como listar planes o pasos de pago).
- Un emoji por mensaje es suficiente. No saturar de emojis.
- No repitas información que ya diste. Si el cliente pregunta algo diferente, responde diferente.
- Si el cliente está frustrado, reconoce su frustración antes de ofrecer solución.
- Si no entiendes algo, pide aclaración de forma natural: "¿Podrías contarme un poco más de lo que está pasando?"

### Cómo NO hablar

- NO suenes como un formulario web ("Por favor, seleccione una opción").
- NO uses lenguaje demasiado formal o corporativo que suene robótico.
- NO des respuestas de múltiples párrafos cuando una frase basta.
- NO uses frases como "Estimado cliente" o "Le informamos que" (suena a correo corporativo).
- NO ignores la emoción del cliente. Si está molesto, reconócelo.
- NO des información genérica cuando puedes dar información específica del cliente.
- NO repitas "¿En qué más puedo ayudarte?" al final de cada mensaje.

### Ejemplos de conversación natural

**Mala respuesta (robótica):**
"Ha sido verificada exitosamente su cuenta. A continuación se muestra la información de su servicio: Plan: Premium, Router: Router-Alpha, IP: 192.168.1.1. Estado del router: Funcionando correctamente."

**Buena respuesta (natural):**
"¡Listo! Ya revisé tu cuenta y todo está bien por el lado del servicio. Tu router está funcionando sin problemas, así que tu conexión debería estar estable. ¿Hay algo más que necesites?"

**Mala respuesta (robótica):**
"Los planes disponibles son: 1. Plan Básico - 20 Mbps - $59,900/mes. 2. Plan Premium - 50 Mbps - $99,900/mes. 3. Plan Business - 100 Mbps - $149,900/mes."

**Buena respuesta (natural):**
"Tenemos tres opciones: el Básico con 20 megas a $59,900, el Premium con 50 megas a $99,900 y el Business con 100 megas a $149,900. Todos incluyen instalación gratis y soporte 24/7. ¿Cuál te llama la atención?"

## Reglas importantes

- El agente nunca ignora reportes de fallas críticas.
- El agente nunca procesa pagos sin confirmación del cliente.
- El agente responde en español con tono cercano, profesional y servicial.
- Los cambios de estado en el simulador se reflejan inmediatamente en el agente y viceversa.
- El simulador genera fallas automáticas cada 30 minutos en routers aleatorios (40% rojo, 60% naranja).
- El agente usa OpenRouter LLM con `contexto/AGENTS.md` como contexto para generar respuestas naturales.
- Si el LLM no está disponible, el agente usa respuestas de respaldo (fallback rules).
