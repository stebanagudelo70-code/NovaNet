================================================================================
 novaNet - Guia de Instalacion y Ejecucion en Local
================================================================================

Este documento explica como instalar el proyecto en un PC para que funcione
en local (en tu propia maquina, sin necesidad de servidores externos).

--------------------------------------------------------------------------------
1. REQUISITOS PREVIOS
--------------------------------------------------------------------------------
- Python 3.9 o superior instalado.
  (Descargalo desde https://www.python.org/downloads/)
- Durante la instalacion de Python marca la casilla "Add Python to PATH".
- (Opcional) PostgreSQL instalado y corriendo en el equipo.
  Si no lo tienes, no pasa nada: el proyecto usa datos de prueba automaticamente.

--------------------------------------------------------------------------------
2. OBTENER EL PROYECTO
--------------------------------------------------------------------------------
- Clona el repositorio o copia la carpeta del proyecto en tu PC:

      git clone <URL_DEL_REPOSITORIO>
      cd NovaNet

--------------------------------------------------------------------------------
3. CREAR EL ENTORNO VIRTUAL (recomendado)
--------------------------------------------------------------------------------
Abre una terminal (PowerShell, CMD o terminal de Linux) dentro de la carpeta
del proyecto y ejecuta:

  Windows:
      python -m venv .novaNet
      .novaNet\Scripts\activate

  Linux / Mac:
      python3 -m venv .novaNet
      source .novaNet/bin/activate

Deberias ver el nombre del entorno "(novaNet)" al inicio de la linea.

--------------------------------------------------------------------------------
4. INSTALAR LAS DEPENDENCIAS
--------------------------------------------------------------------------------
Con el entorno virtual activo, ejecuta:

      pip install -r requirements.txt

Esto instala Flask, Flask-SocketIO, pg8000, requests, pyyaml, etc.

--------------------------------------------------------------------------------
5. CONFIGURAR LAS VARIABLES DE ENTORNO (IMPORTANTE)
--------------------------------------------------------------------------------
Crea un archivo llamado  config/.env  (si no existe) con el siguiente
contenido y completa cada campo con TUS datos:

      OPENROUTER_API_KEY=tu_api_key_aqui
      DB_HOST=localhost
      DB_NAME=clientes_internet
      DB_USER=tu_usuario_db
      DB_PASSWORD=tu_password_db
      DB_PORT=5432

Explicacion de cada campo:
  - OPENROUTER_API_KEY : Clave API de OpenRouter (LLM). Se obtiene en
                         https://openrouter.ai  creando una cuenta.
                         Si la dejas en "tu_api_key_aqui", el agente funciona
                         pero sin inteligencia artificial (usa respuestas
                         de respaldo predefinidas).
  - DB_HOST            : Direccion del servidor PostgreSQL (normalmente localhost).
  - DB_NAME            : Nombre de la base de datos.
  - DB_USER            : Usuario de PostgreSQL.
  - DB_PASSWORD        : Contrasena de ese usuario de PostgreSQL.
  - DB_PORT            : Puerto de PostgreSQL (por defecto 5432).

NOTA: El archivo config/.env NO debe subirse a GitHub (esta en el .gitignore).
      Nunca subas tus claves o contrasenas reales.

Si no tienes PostgreSQL disponible, deja esos valores como estan: el servidor
detectara que no hay base de datos y usara datos de prueba automaticamente.

--------------------------------------------------------------------------------
6. (OPCIONAL) CREAR LA BASE DE DATOS EN POSTGRESQL
--------------------------------------------------------------------------------
Si quieres usar PostgreSQL en lugar de los datos de prueba, crea la base de
datos y la tabla clientes con este SQL:

      CREATE DATABASE clientes_internet;

      CREATE TABLE clientes (
          id SERIAL PRIMARY KEY,
          nombre VARCHAR(100),
          apellido VARCHAR(100),
          cedula VARCHAR(20) UNIQUE,
          router VARCHAR(50),
          ip VARCHAR(20),
          tipo_plan VARCHAR(50)
      );

El proyecto tambien usa las tablas pagos y reportes_falla (las crea solo
si ya existen en tu base de datos; revisa source/backend/database/database.py).

--------------------------------------------------------------------------------
7. EJECUTAR EL SERVIDOR (BACKEND)
--------------------------------------------------------------------------------
Con el entorno virtual activo y dentro de la carpeta del proyecto:

      python source/backend/main.py

Si todo sale bien veras mensajes como:
  [OK] novaNet inicializado
  [OK] 10 routers inicializados
  Servidor: http://localhost:5000

El servidor queda escuchando en el puerto 5000. NO cierres esta terminal
mientras uses el proyecto.

--------------------------------------------------------------------------------
8. ACCEDER A LAS INTERFACES
--------------------------------------------------------------------------------
Con el servidor corriendo, abre tu navegador en:

  - Chat del cliente:    http://127.0.0.1:5000/
  - Simulador de red:    http://127.0.0.1:5000/simulacion

Simulador de red - acceso como tecnico:
  - Usuario: cualquier nombre (ej: juan)
  - Clave:   la definida en source/frontend/simulator/funciones.js
             (variable CLAVE_DEFAULT). Cambiala antes de desplegar.

Clientes de prueba (si usas datos mock, sin PostgreSQL):
  - Cedula 10101010 - Carlos Rodriguez (Router-Alpha)
  - Cedula 20202020 - Maria Garcia    (Router-Bravo)
  - Cedula 30303030 - Pedro Lopez     (Router-Charlie)

--------------------------------------------------------------------------------
9. COMO FUNCIONA EL PROYECTO (RESUMEN)
--------------------------------------------------------------------------------
- El chat del cliente (/) envia mensajes al backend por HTTP POST /chat.
- El agente clasifica la intencion (soporte, pagos, ventas, identificacion).
- Segun el router del cliente, el agente: confirma conexion (verde),
  reinicia el router (naranja) o despacha tecnico (rojo).
- El simulador (/simulacion) se conecta al backend por WebSocket (Socket.IO)
  y sincroniza el estado de los 10 routers en tiempo real.
- El simulador genera fallas automaticas cada 30 minutos.

--------------------------------------------------------------------------------
10. DETENER EL SERVIDOR
--------------------------------------------------------------------------------
En la terminal donde corre el servidor presiona Ctrl + C.

Para desactivar el entorno virtual ejecuta:

      deactivate

================================================================================
Fin de la guia. Si tienes dudas, revisa docs/AGENTS.md.
================================================================================
