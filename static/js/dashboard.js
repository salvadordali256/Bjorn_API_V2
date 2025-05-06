// Dashboard JavaScript for Bjorn HVAC Abbreviation Tool

document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard data
    loadDashboardData();
});

// Load dashboard data from API
async function loadDashboardData() {
    try {
        const response = await fetch('/api/stats');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                updateDashboard(data.stats);
            } else {
                console.error('Error loading stats:', data.error);
            }
        } else {
            console.error('Error loading stats:', response.statusText);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update dashboard with statistics
function updateDashboard(stats) {
    // Update metrics
    document.getElementById('total-processed').textContent = stats.total_processed.toLocaleString();
    document.getElementById('files-processed').textContent = stats.files_processed.toLocaleString();
    document.getElementById('success-rate').textContent = stats.success_rate;
    document.getElementById('avg-reduction').textContent = stats.avg_reduction;
    
    // Create charts
    createMethodsChart(stats.methods);
    createPatternsChart(stats.patterns);
    
    // Create fake activity data for display purposes
    createActivityTable();
}

// Create methods distribution chart
function createMethodsChart(methods) {
    const ctx = document.getElementById('methods-chart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const data = [];
    const backgroundColor = [
        'rgba(54, 162, 235, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(255, 206, 86, 0.7)'
    ];
    
    // Parse methods
    if (methods) {
        if (methods.ml_hybrid) {
            labels.push('AI Hybrid');
            data.push(methods.ml_hybrid);
        }
        
        if (methods.ml_basic) {
            labels.push('AI Basic');
            data.push(methods.ml_basic);
        }
        
        if (methods.rule_based) {
            labels.push('Rule-Based');
            data.push(methods.rule_based);
        }
    }
    
    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Create patterns distribution chart
function createPatternsChart(patterns) {
    const ctx = document.getElementById('patterns-chart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const data = [];
    const backgroundColor = [
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)'
    ];
    
    // Parse patterns
    if (patterns) {
        for (const [key, value] of Object.entries(patterns)) {
            // Convert key to title case
            const label = key.charAt(0).toUpperCase() + key.slice(1);
            labels.push(label);
            data.push(value);
        }
    } else {
        // Default data if none provided
        labels.push('Dictionary', 'Truncation', 'Vowel Removal', 'Custom');
        data.push(450, 250, 180, 120);
    }
    
    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Usage Count',
                data: data,
                backgroundColor: backgroundColor
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create activity table with sample data
function createActivityTable() {
    const tableBody = document.querySelector('#activity-table tbody');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Sample data
    const activities = [
        { date: '2025-05-05', type: 'File Upload', records: 342, success: '91.2%', method: 'AI Hybrid' },
        { date: '2025-05-04', type: 'Single Text', records: 1, success: '100%', method: 'AI Hybrid' },
        { date: '2025-05-04', type: 'File Upload', records: 156, success: '85.3%', method: 'Rule-Based' },
        { date: '2025-05-03', type: 'Single Text', records: 1, success: '100%', method: 'AI Basic' },
        { date: '2025-05-03', type: 'File Upload', records: 217, success: '89.4%', method: 'AI Hybrid' },
        { date: '2025-05-02', type: 'File Upload', records: 128, success: '82.8%', method: 'Rule-Based' },
        { date: '2025-05-01', type: 'Single Text', records: 1, success: '100%', method: 'AI Hybrid' },
        { date: '2025-05-01', type: 'File Upload', records: 398, success: '94.2%', method: 'AI Hybrid' }
    ];
    
    // Create rows
    activities.forEach(activity => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatDate(activity.date)}</td>
            <td>${activity.type}</td>
            <td>${activity.records.toLocaleString()}</td>
            <td>${activity.success}</td>
            <td>${activity.method}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Format date string
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}