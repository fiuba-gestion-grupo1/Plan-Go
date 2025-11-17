// Script simple para probar el formateo de fechas
const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr + 'T00:00:00'); // Forzar medianoche local
    return date.toISOString().split('T')[0];
};

// Simular las fechas que el usuario ingresó
const startDate = '2025-11-17'; // 17 de noviembre
const endDate = '2025-11-20';   // 20 de noviembre

console.log('Fecha inicial ingresada:', startDate);
console.log('Fecha final ingresada:', endDate);
console.log('Fecha inicial después del formateo:', formatDate(startDate));
console.log('Fecha final después del formateo:', formatDate(endDate));

// Verificar qué fecha envía exactamente el navegador
console.log('\nDebugging detallado:');
console.log('Fecha inicial raw:', startDate);
console.log('Date object inicial:', new Date(startDate + 'T00:00:00'));
console.log('ISO string completo:', new Date(startDate + 'T00:00:00').toISOString());
console.log('Solo fecha:', new Date(startDate + 'T00:00:00').toISOString().split('T')[0]);