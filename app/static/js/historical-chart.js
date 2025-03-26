document.addEventListener('DOMContentLoaded', function() {
    // Get the chart canvas element
    const ctx = document.getElementById('historicalDataChart').getContext('2d');
    
    // Initialize chart with empty data
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°F)',
                    data: [],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    ticks: {
                        maxTicksLimit: 12,
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperature (°F)'
                    },
                    min: function(context) {
                        const min = Math.min(...context.chart.data.datasets[0].data);
                        return Math.max(0, Math.floor(min - 5));
                    },
                    max: function(context) {
                        const max = Math.max(...context.chart.data.datasets[0].data);
                        return Math.ceil(max + 5);
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Humidity (%)'
                    },
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            },
            plugins: {
                tooltip: {
                    enabled: true
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Historical Sensor Data'
                }
            }
        }
    });
    
    // Function to fetch and update chart data
    function updateChartData() {
        fetch('/api/chart-data')
            .then(response => response.json())
            .then(data => {
                // Update chart with new data
                chart.data.labels = data.timestamps;
                chart.data.datasets[0].data = data.temperature;
                chart.data.datasets[1].data = data.humidity;
                chart.update();
                
                // Update last fetched time
                const lastUpdated = document.getElementById('chart-last-updated');
                if (lastUpdated) {
                    const now = new Date();
                    lastUpdated.textContent = now.toLocaleTimeString();
                }
            })
            .catch(error => console.error('Error fetching chart data:', error));
    }
    
    // Initial data load
    updateChartData();
    
    // Refresh data every 5 minutes (300000 ms)
    setInterval(updateChartData, 300000);
});
