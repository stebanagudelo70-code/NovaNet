const API_URL = 'http://127.0.0.1:5000/chat';
const HEALTH_URL = 'http://127.0.0.1:5000/health';

let serverAvailable = false;
let sessionId = 'session_' + Date.now();

const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');

async function init() {
    await checkServerConnection();

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const intent = btn.getAttribute('data-intent');
            handleQuickAction(intent);
        });
    });

    messageInput.focus();
}

async function checkServerConnection() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const response = await fetch(HEALTH_URL, {
            signal: controller.signal,
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            serverAvailable = true;
            updateStatus(true);
            return true;
        } else {
            throw new Error('Respuesta no válida');
        }
    } catch (error) {
        serverAvailable = false;
        updateStatus(false);
        return false;
    }
}

function updateStatus(online) {
    const statusElement = document.querySelector('.status');
    if (statusElement) {
        if (online) {
            statusElement.innerHTML = '🟢 En línea - Soporte técnico, pagos y ventas';
            statusElement.style.color = '#10b981';
        } else {
            statusElement.innerHTML = '🔴 Sin conexión (offline)';
            statusElement.style.color = '#ef4444';
        }
    }
}

function handleQuickAction(intent) {
    const messages = {
        soporte: 'Necesito reportar una falla en mi servicio de internet',
        pagos: 'Quiero realizar un pago',
        ventas: '¿Qué planes de internet tienen disponibles?'
    };

    const message = messages[intent] || '';
    if (message) {
        messageInput.value = message;
        sendMessage();
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    messageInput.value = '';
    messageInput.focus();

    addMessage(message, 'user', false);

    showTypingIndicator();

    try {
        let response;

        if (serverAvailable) {
            response = await sendToServer(message);
        } else {
            response = getFallbackResponse(message);
        }

        hideTypingIndicator();
        addMessage(response, 'bot', true);

    } catch (error) {
        hideTypingIndicator();
        console.error('Error:', error);

        if (serverAvailable) {
            serverAvailable = false;
            updateStatus(false);
        }

        const offlineResponse = getFallbackResponse(message);
        addMessage(offlineResponse, 'bot', true);
    }
}

async function sendToServer(message) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        return data.response;

    } catch (error) {
        console.error('Error en petición:', error);
        throw error;
    }
}

function getFallbackResponse(message) {
    const lowerMsg = message.toLowerCase();

    if (lowerMsg.includes('falla') || lowerMsg.includes('no funciona') || lowerMsg.includes('soporte')) {
        return "🔧 **Soporte Técnico** (Modo offline)\n\nLamento que tengas problemas. Para ayudarte con tu falla, necesito tu cédula de cliente y una breve descripción de lo que está pasando.\n\nConecta el servidor para que pueda revisar el estado de tu router en tiempo real.";
    }

    if (lowerMsg.includes('pago') || lowerMsg.includes('pagar') || lowerMsg.includes('factura')) {
        return "💳 **Pagos** (Modo offline)\n\nPuedes pagar con Mercado Pago o Visa. Ambos son rápidos y seguros.\n\nConecta el servidor para procesar tu pago directamente.";
    }

    if (lowerMsg.includes('plan') || lowerMsg.includes('planes') || lowerMsg.includes('velocidad')) {
        return "📦 **Planes de Internet** (Modo offline)\n\nTenemos tres opciones:\n• **Básico**: 20 megas a $59,900/mes\n• **Premium**: 50 megas a $99,900/mes\n• **Business**: 100 megas a $149,900/mes\n\nTodos incluyen instalación gratis y soporte 24/7. ¿Cuál te interesa?";
    }

    if (lowerMsg.includes('hola') || lowerMsg.includes('buenos')) {
        return "🤖 ¡Hola! Bienvenido a **novaNet**.\n\n¿En qué puedo ayudarte?\n• 🔧 Soporte técnico\n• 💳 Pagos\n• 📦 Planes de internet";
    }

    return "🤖 ¡Hola! Bienvenido a **novaNet**.\n\nPuedo ayudarte con:\n• 🔧 **Soporte técnico** - Reportar fallas\n• 💳 **Pagos** - Realizar pagos\n• 📦 **Planes** - Ver nuestros planes\n\nEscribe tu consulta y con gusto te atenderé.";
}

let messageHistory = [];

function addMessage(content, sender, isHtml = false, skipSave = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'bot' ? '🛡️' : '👤';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (isHtml && sender === 'bot') {
        let cleanContent = content;
        cleanContent = cleanContent.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');
        bubble.innerHTML = cleanContent;
    } else {
        const textContent = document.createTextNode(content);
        bubble.appendChild(textContent);
    }

    messageContent.appendChild(bubble);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

setInterval(async () => {
    if (!serverAvailable) {
        const wasAvailable = serverAvailable;
        await checkServerConnection();

        if (!wasAvailable && serverAvailable) {
            addMessage('✅ **Conexión restablecida**\n\nEl servidor de novaNet está disponible.', 'bot', true);
            updateStatus(true);
        }
    }
}, 15000);

init();
