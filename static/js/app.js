/**
 * QueVendí PRO - JavaScript Principal
 * Versión simplificada para trabajar con HTMX y HTML directo
 */

// ========================================
// CONFIGURACIÓN
// ========================================

console.log('✅ QueVendí PRO inicializado');

// ========================================
// FUNCIONES AUXILIARES (si las necesitas)
// ========================================

function showConfig() {
    alert('Configuración próximamente...');
}

// ========================================
// HTMX EVENTS (opcional - solo para debugging)
// ========================================

// Loggear eventos HTMX para debugging
document.addEventListener('htmx:afterSwap', function(event) {
    console.log('[HTMX] Contenido actualizado:', event.detail.target.id);
});

document.addEventListener('htmx:responseError', function(event) {
    console.error('[HTMX] Error en respuesta:', event.detail);
});

// ========================================
// NOTAS:
// ========================================
// Ya NO necesitas:
// - renderDailySummary() → El HTML viene del backend
// - renderSalesList() → El HTML viene del backend
// - JSON.parse() → Ya no parseamos JSON, HTMX inserta HTML directo
//
// El flujo ahora es:
// 1. HTMX hace GET /api/sales/today/html
// 2. Backend devuelve HTML completo
// 3. HTMX lo inserta directamente en el DOM
// 4. ¡Listo! No necesitas JavaScript adicional