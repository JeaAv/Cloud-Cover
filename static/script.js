var map = L.map('map').setView([7.8592, 125.0515], 13);
var currentMarker = null;
let hourlyChart;

// Add tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

// Function to create or update a chart
function createOrUpdateChart(chart, ctx, labels, data, label) {
    if (chart) {
        // Clear existing data
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        
        chart.data.labels.push(...labels);
        chart.data.datasets[0].data.push(...data);
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true }
                }
            }
        });
    }
    return chart;
}

// Function to handle map click
function handleMapClick(e) {
    var lat = e.latlng.lat.toFixed(6);
    var lng = e.latlng.lng.toFixed(6);

    fetchCloudCoverData(lat, lng);
}

// Toggle data container visibility
//document.getElementById('cloudCoverBtn').addEventListener('click', function () {
 //   var container = document.querySelector('.data-container');
 //   container.style.display = (container.style.display === 'none' || container.style.display === '') ? 'block' : 'none';
//});

// Add event listener for Exit button
//document.getElementById('exitBtn').addEventListener('click', function () {
//    document.querySelector('.data-container').style.display = 'none';
//});


// Fetch cloud cover data from server
function fetchCloudCoverData(lat, lng) {
    fetch('/get-stored-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: lat, longitude: lng })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Fetched Data:', data);  // Add this line for debugging
        
        if (data.success) {
            updateCloudCoverData(data.current);
            document.getElementById('latitude').innerText = lat;
            document.getElementById('longitude').innerText = lng;

            if (currentMarker) map.removeLayer(currentMarker);
            currentMarker = L.marker([lat, lng]).addTo(map)
                .bindPopup(`Latitude: ${lat}<br>Longitude: ${lng}`)
                .openPopup();

            // Plot hourly cloud cover data
            const hourlyCtx = document.getElementById('hourlyCloudCoverChart').getContext('2d');
            hourlyChart = createOrUpdateChart(
                hourlyChart,
                hourlyCtx,
                data.hourly.time,
                data.hourly.cloud_cover_total, // Correcting to match your data structure
                'Hourly Cloud Cover'
            );
        } else {
            alert(data.message || 'No data found for this location.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching data. Please try again.');
    });
}

// Update cloud cover data in the table
function updateCloudCoverData(data) {
    document.getElementById('cloudCoverTotal').innerText = data.cloud_cover_total || 'N/A';
    document.getElementById('cloudCoverLow').innerText = data.cloud_cover_low || 'N/A';
    document.getElementById('cloudCoverMid').innerText = data.cloud_cover_mid || 'N/A';
    document.getElementById('cloudCoverHigh').innerText = data.cloud_cover_high || 'N/A';
    document.getElementById('visibility').innerText = data.visibility || 'N/A';
}

// Event listener for map clicks
map.on('click', handleMapClick);

// Document ready for toggle chart button
document.addEventListener("DOMContentLoaded", function () {
    const toggleChartButton = document.getElementById('toggleChartButton');
    const chartContainer = document.getElementById('chartContainer');
    
    let chartVisible = false;

    // Function to toggle chart visibility
    toggleChartButton.addEventListener('click', function () {
        chartVisible = !chartVisible;
        chartContainer.style.display = chartVisible ? 'block' : 'none';
        toggleChartButton.textContent = chartVisible ? 'Hide Cloud Cover Data' : 'Show Cloud Cover Data';

        console.log('Chart visibility toggled:', chartVisible);  // Add this line for debugging
    });
});

// Handle logout button click
document.getElementById('logout-btn').addEventListener('click', function() {
    // Clear session data if necessary
    sessionStorage.clear(); // Uncomment if you're using session storage

    // Redirect to the login page
    window.location.href = '/'; // Adjust this URL based on your login route
});

// Handle user page button click
document.getElementById('userPageBtn').addEventListener('click', function() {
    // Redirect to user page
    window.location.href = '/all-users'; // Adjust this URL based on your route to user.html
});

