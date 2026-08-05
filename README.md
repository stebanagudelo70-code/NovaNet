📖 NovaNet es un agente conversacional de atención al cliente para un proveedor de internet (ISP). Funciona como asesor digital a través de un chat web, integrando soporte técnico, pagos y ventas en un mismo sistema.

🎯 Funcionalidades principales
Soporte técnico  
Diagnostica fallas consultando el estado real del router del cliente:

Falla menor → reinicio automático.

Falla crítica → despacho de técnico.

Pagos online  
Procesa pagos simulados con Mercado Pago o Visa, siempre con confirmación explícita del cliente.

Gestión de planes  
Presenta y adapta planes de servicio (Básico, Premium, Business).

Identificación de cliente  
Verifica la cuenta por cédula y consulta el router en la simulación de red.

Simulador de red  
Panel del técnico sincronizado en tiempo real vía WebSocket, con estadísticas, alertas e historial.

⚙️ Tecnologías utilizadas
Backend (Python)

Flask (API REST)

Flask-SocketIO + Simple-WebSocket (tiempo real)

OpenRouter API (LLM)

PostgreSQL con pg8000 (fallback a datos mock)

python-dotenv (variables de entorno)

PyYAML (identidad del agente)

Frontend (HTML/CSS/JS vanilla)

Chat del cliente con modo offline y reconexión automática

Simulador con Socket.IO client

Estadísticas, alertas e historial

🧩 Metodologías y patrones
Arquitectura en capas: API / base de datos / herramientas (red, pagos, memoria) / frontend.

Patrón fallback: degradación elegante (sin LLM → respuestas predefinidas; sin PostgreSQL → datos mock).

Simulación / fake-it: para pagos y red.

Arquitectura orientada a eventos: cambios de router notifican listeners y se transmiten por WebSocket.

Memoria de sesión con TTL: contexto conversacional con expiración y limpieza automática.

Diseño conversacional: tono humano estilo WhatsApp/Messenger con reglas de voz explícitas.

Configuración 12-factor: credenciales y variables fuera del código.

Este bloque está listo para insertarse como README.md → sección inferior en tu repositorio GitHub.

¿Quieres que lo prepare también con un diagrama ASCII simplificado para acompañar la descripción en el README, como complemento visual al esquema que ya tienes en la imagen?

organiza la descripcion de una manera mas profesional
Aquí tienes una versión más profesional y estructurada de la descripción de NovaNet, lista para integrarse en la sección inferior de tu README en GitHub. Está organizada con un estilo formal de documentación técnica, siguiendo buenas prácticas de presentación en proyectos open source.

📘 NovaNet – Descripción del Sistema
NovaNet es un agente conversacional diseñado para la atención al cliente de un proveedor de servicios de internet (ISP). Su propósito es centralizar soporte técnico, gestión de pagos y ventas en una única plataforma digital, ofreciendo una experiencia cercana y eficiente.

🎯 Funcionalidades principales
Soporte técnico

Diagnóstico de fallas en routers mediante simulación en tiempo real.

Falla menor → reinicio automático.

Falla crítica → despacho de técnico.

Gestión de pagos

Procesamiento de pagos simulados con Mercado Pago y Visa.

Confirmación explícita requerida por parte del cliente.

Ventas y planes

Presentación y adaptación de planes de servicio: Básico, Premium y Business.

Identificación de clientes

Validación por cédula y verificación de cuenta.

Consulta del estado del router en la simulación de red.

Simulador de red

Panel técnico sincronizado vía WebSocket.

Estadísticas, alertas e historial de eventos.

⚙️ Tecnologías utilizadas
Backend (Python)

Flask (API REST).

Flask-SocketIO + Simple-WebSocket (comunicación en tiempo real).

OpenRouter API (LLM).

PostgreSQL con pg8000 (fallback a datos mock).

python-dotenv (gestión de variables de entorno).

PyYAML (configuración e identidad del agente).

Frontend (HTML/CSS/JS vanilla)

Chat web con modo offline y reconexión automática.

Simulador técnico con Socket.IO client.

Visualización de estadísticas, alertas e historial.

<img width="1230" height="819" alt="Readme" src="https://github.com/user-attachments/assets/4060703d-493b-4dba-bd8c-d35a7c3dfbda" />

🧩 Metodologías y patrones de diseño
Arquitectura en capas: separación entre API, base de datos, herramientas (red, pagos, memoria) y frontend.

Patrón fallback: degradación controlada (sin LLM → respuestas predefinidas; sin PostgreSQL → datos mock).

Simulación / fake-it: para pagos y red.

Arquitectura orientada a eventos: cambios en routers notifican listeners y se transmiten por WebSocket.

Memoria de sesión con TTL: contexto conversacional con expiración y limpieza automática.

Diseño conversacional: tono humano estilo WhatsApp/Messenger con reglas de voz explícitas.



