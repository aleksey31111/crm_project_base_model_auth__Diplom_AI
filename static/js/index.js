// static/js/index.js
document.addEventListener('DOMContentLoaded', function() {
    // График выручки
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    new Chart(revenueCtx, {
        type: 'line',
        data: {
            labels: window.chartData.months,
            datasets: [{
                label: 'Выручка (₽)',
                data: window.chartData.revenues,
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                tooltip: { callbacks: { label: (ctx) => `${ctx.raw.toLocaleString()} ₽` } }
            }
        }
    });

    // Круговая диаграмма статусов задач
    const statusCtx = document.getElementById('taskStatusChart').getContext('2d');
    new Chart(statusCtx, {
        type: 'pie',
        data: {
            labels: window.chartData.statusLabels,
            datasets: [{
                data: window.chartData.statusData,
                backgroundColor: ['#1cc88a', '#4e73df', '#f6c23e', '#e74a3b']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });
});