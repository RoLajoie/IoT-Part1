let temperatureGauge;
let humidityGauge;
  
window.onload = () => {
    // Initialize everything first
    initializeGauges();

    document.getElementById('toggle-switch').addEventListener('change', function() {
        let newState = this.checked ? 'ON' : 'OFF';
        fetch(`/toggle_led/${newState}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => updateLED(data.led_status));
    });

    setInterval(fetchData, 5000);
    updateLED("{{ led_status }}");
    updateFan("{{ fan_status }}");
};

function initializeGauges() {
    temperatureGauge = new JustGage({
        id: "temperature-gauge",
        value: -1,
        decimals: 1,
        min: 15,
        max: 30,
        title: "Temperature",
        symbol: "°C",
        gaugeWidthScale: 0.5,
        pointer: true,
    });

    humidityGauge = new JustGage({
        id: "humidity-gauge",
        donut: true,
        value: -1,
        decimals: 1,
        min: 0,
        max: 100,
        title: "Humidity",
        symbol: "%",
        gaugeWidthScale: 0.5,
        levelColors: ["#b5e8f5", "#2e98b3", "#0000ff"],
    });
}

function fetchData() {
    fetch('/sensor_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.temperature && data.humidity) {
                // Update the gauges with values
                temperatureGauge.refresh(data.temperature);
                humidityGauge.refresh(data.humidity);

                // Check if the fan should be toggled ON
                updateFan("{{ fan_status }}", "{{ fan_switch_requested }}");
            }
        })
        .catch(error => console.error('Error fetching sensor data:', error));
}

function updateLED(ledStatus) {
    // Defining the variables
    const lightImage = document.getElementById('light-image');
    const toggleSwitch = document.getElementById('toggle-switch');

    // Assigning the variables and displaying on the page
    toggleSwitch.checked = (ledStatus === 'ON');
    lightImage.src = (ledStatus === 'ON') ? ('/static/images/lit.png') : ('/static/images/dark.png');
    // If not received yet, don't want to display "{{ led_status }}"
    // TODO: confirm if better to just set to dark if waiting
    if (ledStatus === "{{ led_status }}") {
        document.getElementById('led-status').textContent = "LED Status: Waiting...";
    } else {
        document.getElementById('led-status').textContent = "LED Status: " + ledStatus;
    }
    lightImage.className = (ledStatus === 'ON') ? 'lit' : 'dark';
}


function updateFan(fanStatus, fanSwitchRequested) {
    const fanIcon = document.getElementById('fan-icon');

    fanIcon.src = (fanStatus === 'ON' && fanSwitchRequested) ? ('/static/images/fan-on.webp') : ('/static/images/fan-off.webp');
    // If not received yet, don't want to display "{{ fan_status }}"
    // TODO: confirm if better to just set to off if waiting
    if (fanStatus === "{{ fan_status }}") {
        document.getElementById('fan-status').textContent = "Fan Status: Waiting...";
    } else {
        document.getElementById('fan-status').textContent = "Fan Status: " + fanStatus;
    }
}