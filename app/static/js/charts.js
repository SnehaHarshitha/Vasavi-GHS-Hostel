// Dashboard Chart Rendering Utilities using Chart.js

function renderFoodChoiceChart(canvasId, eggCount, vegCount, pendingCount) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Egg', 'Vegetarian', 'Pending Choice'],
            datasets: [{
                data: [eggCount, vegCount, pendingCount],
                backgroundColor: ['#f59e0b', '#10b981', '#94a3b8'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderCleaningCompletionChart(canvasId, completed, pending) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Cleaned Today', 'Pending / Missed'],
            datasets: [{
                data: [completed, pending],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderComplaintBreakdownChart(canvasId, categoryData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(categoryData),
            datasets: [{
                label: 'Complaints by Category',
                data: Object.values(categoryData),
                backgroundColor: '#1e3a8a',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
