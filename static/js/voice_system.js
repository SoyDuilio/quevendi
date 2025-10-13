/**
 * SISTEMA DE VOZ SIMPLIFICADO - QueVendí PRO
 * Flujo: Escuchar → Procesar → Responder → Esperar siguiente comando
 */

// Estado global
let recognition;
let isListening = false;
let cart = [];
let paymentMethod = 'efectivo'; // efectivo, yape, plin
let voiceSettings = {
    voice: 'es-PE-Standard-A',
    speed: 1.0,
    enabled: true
};

// Configuración
const API_BASE = '';
const IDLE_TIMEOUT = 180000; // 3 minutos
let idleTimer = null;

/**
 * INICIALIZACIÓN
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[VoiceSystem] Inicializando...');
    
    initSpeechRecognition();
    initPaymentButtons();
    initVoiceSettings();
    loadVoiceSettings();
    startIdleMonitor();
    
    // Auto-iniciar micrófono
    setTimeout(() => {
        startListening();
    }, 1000);
    
    console.log('[VoiceSystem] ✅ Sistema listo');

    // Permitir click en el estado para reactivar
    const micStatus = document.getElementById('mic-status');
    if (micStatus) {
        micStatus.addEventListener('click', function() {
            if (!isListening) {
                console.log('[Voice] Reactivando micrófono...');
                startListening();
            }
        });
        micStatus.style.cursor = 'pointer';
    }
});

/**
 * RECONOCIMIENTO DE VOZ
 */
function initSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showError('Navegador no soporta reconocimiento de voz');
        return false;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    recognition.lang = 'es-PE';
    recognition.continuous = true; // ← CLAVE: Escucha continua
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    recognition.onstart = () => {
        console.log('[Voice] 🎤 Escuchando...');
        isListening = true;
        updateMicStatus(true);
        resetIdleTimer();
    };
    
    recognition.onresult = (event) => {
        const resultIndex = event.resultIndex;
        const transcript = event.results[resultIndex][0].transcript.trim();
        console.log('[Voice] 📝 Transcripción:', transcript);
        
        showTranscript(transcript);
        processCommand(transcript);
        resetIdleTimer();
    };
    
    recognition.onerror = (event) => {
        console.error('[Voice] ❌ Error:', event.error);
        
        if (event.error === 'no-speech') {
            console.log('[Voice] Sin voz detectada, continuando...');
        } else if (event.error === 'not-allowed') {
            showError('Permiso de micrófono denegado');
            isListening = false;
            updateMicStatus(false);
        } else {
            console.warn('[Voice] Error:', event.error);
        }
    };
    
    recognition.onend = () => {
        console.log('[Voice] Reconocimiento terminado');
        
        // Auto-reiniciar si debería estar escuchando
        if (isListening) {
            console.log('[Voice] 🔄 Reiniciando reconocimiento...');
            setTimeout(() => {
                try {
                    recognition.start();
                } catch (e) {
                    console.warn('[Voice] Error al reiniciar:', e);
                }
            }, 300);
        } else {
            updateMicStatus(false);
        }
    };
    
    return true;
}

function startListening() {
    if (!recognition) return;
    
    try {
        recognition.start();
        console.log('[Voice] Iniciado');
    } catch (error) {
        if (error.message.includes('already started')) {
            console.log('[Voice] Ya está escuchando');
        } else {
            console.error('[Voice] Error al iniciar:', error);
        }
    }
}

function stopListening() {
    if (!recognition) return;
    
    isListening = false;
    try {
        recognition.stop();
        console.log('[Voice] Detenido');
    } catch (error) {
        console.warn('[Voice] Error al detener:', error);
    }
}

/**
 * PROCESAMIENTO DE COMANDOS
 */
async function processCommand(text) {
    console.log('[Voice] 🔄 Procesando:', text);
    
    try {
        const response = await fetch(`${API_BASE}/sales/voice/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        console.log('[Voice] 📦 Respuesta:', data);
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al procesar comando');
        }
        
        await handleCommand(data);
        
    } catch (error) {
        console.error('[Voice] ❌ Error:', error);
        await speak(`No entendí ese comando. ${error.message}`);
        playSound('error');
    }
}

async function handleCommand(data) {
    const type = data.type;
    
    switch (type) {
        case 'cancel':
            await handleCancel();
            break;
        
        case 'confirm':
            await handleConfirm();
            break;
        
        case 'add':
            await handleAdd(data);
            break;
        
        case 'sale':
            await handleSale(data);
            break;
        
        case 'change_price':
            await handlePriceChange(data);
            break;
        
        case 'change_product':
            await handleProductChange(data);
            break;
        
        default:
            console.warn('[Voice] Tipo de comando desconocido:', type);
    }
}

async function handleCancel() {
    if (cart.length === 0) {
        await speak('No hay productos en el carrito');
        return;
    }
    
    cart = [];
    updateCartDisplay();
    await speak('Venta cancelada');
    playSound('cancel');
}

async function handleConfirm() {
    if (cart.length === 0) {
        await speak('No hay productos para confirmar');
        return;
    }
    
    await confirmSale();
}

async function handleAdd(data) {
    // Agregar al carrito existente
    for (const item of data.items) {
        cart.push(item);
    }
    
    updateCartDisplay();
    
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    const itemNames = data.items.map(i => `${formatQuantity(i.quantity)} ${i.product.name}`).join(' y ');
    
    await speak(`Agregado ${itemNames}. Van ${formatPrice(total)}`);
    
    if (data.warning) {
        await speak(data.warning);
    }
}

async function handleSale(data) {
    // Reemplazar carrito (nueva venta)
    cart = data.items;
    updateCartDisplay();
    
    const total = data.total;
    const itemNames = data.items.map(i => `${formatQuantity(i.quantity)} ${i.product.name}`).join(' y ');
    
    await speak(`${itemNames}. Van ${formatPrice(total)}`);
    
    if (data.warning) {
        await speak(data.warning);
    }
}

async function handlePriceChange(data) {
    const productQuery = data.product_query;
    const newPrice = data.new_price;
    
    // Buscar producto en el carrito
    const item = cart.find(i => 
        i.product.name.toLowerCase().includes(productQuery) ||
        productQuery.includes(i.product.name.toLowerCase())
    );
    
    if (!item) {
        await speak(`No encontré ${productQuery} en el carrito`);
        return;
    }
    
    const oldPrice = item.product.price;
    item.product.price = newPrice;
    item.subtotal = item.quantity * newPrice;
    
    updateCartDisplay();
    
    const total = cart.reduce((sum, i) => sum + i.subtotal, 0);
    await speak(`Precio de ${item.product.name} cambiado de ${formatPrice(oldPrice)} a ${formatPrice(newPrice)}. Nuevo total: ${formatPrice(total)}`);
}

async function handleProductChange(data) {
    const oldProduct = data.old_product;
    const newProduct = data.new_product;
    
    // Buscar y reemplazar en carrito
    const itemIndex = cart.findIndex(i => i.product.id === oldProduct.id);
    
    if (itemIndex === -1) {
        await speak(`No encontré ${oldProduct.name} en el carrito`);
        return;
    }
    
    const quantity = cart[itemIndex].quantity;
    cart[itemIndex] = {
        product: newProduct,
        quantity: quantity,
        subtotal: quantity * newProduct.price
    };
    
    updateCartDisplay();
    await speak(`Cambiado ${oldProduct.name} por ${newProduct.name}`);
}

/**
 * CONFIRMAR VENTA
 */
async function confirmSale() {
    console.log('[Voice] 💾 Confirmando venta...');
    
    const saleData = {
        items: cart.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity,
            unit_price: item.product.price,
            subtotal: item.subtotal
        })),
        payment_method: paymentMethod,
        payment_reference: null,
        customer_name: null,
        is_credit: false
    };
    
    try {
        const response = await fetch(`${API_BASE}/sales/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(saleData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar venta');
        }
        
        const result = await response.json();
        console.log('[Voice] ✅ Venta guardada:', result);
        
        const total = cart.reduce((sum, i) => sum + i.subtotal, 0);
        
        // Limpiar carrito
        cart = [];
        updateCartDisplay();
        
        // Actualizar UI
        htmx.ajax('GET', '/sales/today/total', {target: '#daily-summary', swap: 'innerHTML'});
        htmx.ajax('GET', '/sales/today', {target: '#sales-list', swap: 'innerHTML'});
        
        // Respuesta de voz
        await speak(`Venta confirmada por ${formatPrice(total)}. Siguiente cliente`);
        playSound('confirm');
        
    } catch (error) {
        console.error('[Voice] ❌ Error al confirmar:', error);
        await speak(`Error al guardar venta: ${error.message}`);
        playSound('error');
    }
}

/**
 * TEXT-TO-SPEECH (VOZ DEL SISTEMA)
 */
async function speak(text) {
    if (!voiceSettings.enabled) {
        console.log('[TTS] Voz deshabilitada');
        return;
    }
    
    console.log('[TTS] 🔊 Diciendo:', text);
    
    try {
        // Intentar Google TTS primero
        const response = await fetch(`${API_BASE}/voice/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice: voiceSettings.voice,
                speed: voiceSettings.speed
            })
        });
        
        const data = await response.json();
        
        if (data.method === 'google_tts' && data.audio) {
            // Reproducir audio de Google TTS
            playAudioBase64(data.audio);
        } else {
            // Fallback a Web Speech API
            speakWithWebAPI(text);
        }
        
    } catch (error) {
        console.error('[TTS] Error:', error);
        // Fallback a Web Speech API
        speakWithWebAPI(text);
    }
}

function speakWithWebAPI(text) {
    if (!('speechSynthesis' in window)) {
        console.warn('[TTS] Web Speech API no disponible');
        return;
    }
    
    // Cancelar cualquier síntesis en curso
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-PE';
    utterance.rate = voiceSettings.speed;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;
    
    // Intentar usar voz específica si está disponible
    const voices = window.speechSynthesis.getVoices();
    const spanishVoice = voices.find(v => v.lang.startsWith('es'));
    if (spanishVoice) {
        utterance.voice = spanishVoice;
    }
    
    window.speechSynthesis.speak(utterance);
}

function playAudioBase64(base64Audio) {
    const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
    audio.play().catch(error => {
        console.error('[TTS] Error reproduciendo audio:', error);
    });
}

/**
 * INTERFAZ DE USUARIO
 */
function updateCartDisplay() {
    const cartContainer = document.getElementById('cart-display');
    if (!cartContainer) return;
    
    if (cart.length === 0) {
        cartContainer.innerHTML = `
            <div class="cart-empty">
                <div class="empty-icon">🛒</div>
                <div class="empty-text">Carrito vacío</div>
                <div class="empty-hint">Di: "un café y 10 panes"</div>
            </div>
        `;
        return;
    }
    
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    
    let itemsHTML = '';
    cart.forEach((item, index) => {
        itemsHTML += `
            <div class="cart-item">
                <div class="item-info">
                    <span class="item-qty">${formatQuantity(item.quantity)}x</span>
                    <span class="item-name">${item.product.name}</span>
                </div>
                <div class="item-price">S/ ${item.subtotal.toFixed(2)}</div>
            </div>
        `;
    });
    
    cartContainer.innerHTML = `
        <div class="cart-items">
            ${itemsHTML}
        </div>
        <div class="cart-total">
            <span class="total-label">TOTAL:</span>
            <span class="total-amount">S/ ${total.toFixed(2)}</span>
        </div>
    `;
}

function updateMicStatus(listening) {
    const statusDiv = document.getElementById('mic-status');
    if (!statusDiv) return;
    
    if (listening) {
        statusDiv.innerHTML = '🎤 ESCUCHANDO...';
        statusDiv.className = 'mic-status listening';
    } else {
        statusDiv.innerHTML = '🎤 PAUSADO';
        statusDiv.className = 'mic-status paused';
    }
}

function showTranscript(text) {
    const transcriptDiv = document.getElementById('transcript');
    if (!transcriptDiv) return;
    
    transcriptDiv.textContent = `"${text}"`;
    transcriptDiv.style.display = 'block';
    
    // Ocultar después de 3 segundos
    setTimeout(() => {
        transcriptDiv.style.display = 'none';
    }, 3000);
}

function showError(message) {
    console.error('[Error]', message);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-toast';
    errorDiv.innerHTML = `
        <div class="error-icon">⚠️</div>
        <div class="error-message">${message}</div>
    `;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => errorDiv.classList.add('show'), 10);
    
    setTimeout(() => {
        errorDiv.classList.remove('show');
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}

/**
 * MÉTODOS DE PAGO
 */
function initPaymentButtons() {
    const paymentButtons = document.querySelectorAll('.payment-btn');
    
    paymentButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const method = this.dataset.method;
            setPaymentMethod(method);
        });
    });
}

function setPaymentMethod(method) {
    paymentMethod = method;
    
    // Actualizar UI
    document.querySelectorAll('.payment-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.method === method) {
            btn.classList.add('active');
        }
    });
    
    console.log('[Payment] Método:', method);
}

/**
 * CONFIGURACIÓN DE VOZ
 */
function initVoiceSettings() {
    const settingsBtn = document.getElementById('voice-settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openVoiceSettings);
    }
}

function openVoiceSettings() {
    // TODO: Abrir modal con configuración
    console.log('[Settings] Abriendo configuración de voz');
}

async function loadVoiceSettings() {
    try {
        const response = await fetch(`${API_BASE}/voice/settings`);
        const data = await response.json();
        
        voiceSettings = {
            voice: data.voice || 'es-PE-Standard-A',
            speed: data.speed || 1.0,
            enabled: data.enabled !== false
        };
        
        console.log('[Settings] Configuración cargada:', voiceSettings);
    } catch (error) {
        console.warn('[Settings] Error cargando configuración:', error);
    }
}

async function saveVoiceSettings(settings) {
    try {
        await fetch(`${API_BASE}/voice/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        voiceSettings = settings;
        console.log('[Settings] Configuración guardada');
    } catch (error) {
        console.error('[Settings] Error guardando configuración:', error);
    }
}

/**
 * MONITOR DE INACTIVIDAD
 */
function startIdleMonitor() {
    resetIdleTimer();
}

function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer);
    
    idleTimer = setTimeout(() => {
        console.log('[Idle] ⏰ Tiempo de inactividad alcanzado');
        checkIdleAlerts();
    }, IDLE_TIMEOUT);
}

async function checkIdleAlerts() {
    try {
        const response = await fetch(`${API_BASE}/sales/stats/today`);
        const stats = await response.json();
        
        // Verificar si hay carrito sin confirmar
        if (cart.length > 0) {
            await speak('Hay un pedido sin terminar');
            playSound('alert');
        }
        
        // Verificar ventas lentas
        if (stats.sales_count < 5) {
            console.log('[Alert] Pocas ventas hoy');
        }
        
        // Verificar productos agotados
        if (stats.low_stock && stats.low_stock.length > 0) {
            const outOfStock = stats.low_stock.filter(p => p.stock === 0);
            if (outOfStock.length > 0) {
                const names = outOfStock.map(p => p.name).join(', ');
                await speak(`Productos agotados: ${names}`);
                playSound('alert');
            }
        }
        
    } catch (error) {
        console.error('[Idle] Error verificando alertas:', error);
    }
}

/**
 * SONIDOS DEL SISTEMA
 */
function playSound(type) {
    // Solo reproducir sonidos si NO está hablando
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
        console.log('[Sound] Esperando a que termine de hablar...');
        setTimeout(() => playSound(type), 500);
        return;
    }
    
    const sounds = {
        'confirm': '/static/sounds/confirm.mp3',
        'cancel': '/static/sounds/cancel.mp3',
        'alert': '/static/sounds/alert.mp3',
        'error': '/static/sounds/error.mp3'
    };
    
    const soundFile = sounds[type];
    if (!soundFile) return;
    
    const audio = new Audio(soundFile);
    audio.volume = 0.3; // Bajado de 0.5 a 0.3
    audio.play().catch(e => console.warn('[Sound] Error:', e));
}

/**
 * UTILIDADES
 */
function formatQuantity(qty) {
    if (qty % 1 === 0) {
        return qty.toString();
    }
    return qty.toFixed(2).replace(/\.?0+$/, '');
}

function formatPrice(price) {
    const soles = Math.floor(price);
    const centavos = Math.round((price - soles) * 100);
    
    if (centavos === 0) {
        return `${soles} ${soles === 1 ? 'sol' : 'soles'}`;
    }
    
    return `${soles} soles con ${centavos} centavos`;
}

/**
 * EXPORTAR FUNCIONES GLOBALES
 */
window.VoiceSystem = {
    startListening,
    stopListening,
    speak,
    setPaymentMethod,
    saveVoiceSettings
};



/**
 * MODAL DE COMANDOS
 */
function openCommandsModal() {
    const modal = document.getElementById('voice-commands-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

function closeCommandsModal() {
    const modal = document.getElementById('voice-commands-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Exportar globalmente
window.openCommandsModal = openCommandsModal;
window.closeCommandsModal = closeCommandsModal;