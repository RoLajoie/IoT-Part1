let temperatureGauge;
let humidityGauge;
let luminosityGauge;
  
window.onload = () => {
    // TODO: if extra time, better to put a loader until there's info
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

    luminosityGauge = new JustGage({
        id: "luminosity-gauge",
        value: -1,
        min: 0,
        max: 1000,
        reverse: true,
        title: "Luminosity",
        gaugeWidthScale: 0.5,
        levelColors: ["#2a2a2a","#d1cfb6", "#f7f697"],
    });
}

function fetchData() {
    fetch('/sensor_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.temperature && data.humidity && data.luminosity) {
                // Update the gauges with values
                temperatureGauge.refresh(data.temperature);
                humidityGauge.refresh(data.humidity);
                luminosityGauge.refresh(data.luminosity);

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
    // TODO: ideally would display only the passed info
    // If not received yet, don't want to display "{{ led_status }}"
    if (ledStatus === "{{ led_status }}") {
        document.getElementById('led-status').textContent = "LED Status: OFF";
    } else {
        document.getElementById('led-status').textContent = "LED Status: " + ledStatus;
    }
    lightImage.className = (ledStatus === 'ON') ? 'lit' : 'dark';
}


function updateFan(fanStatus, fanSwitchRequested) {
    const fanIcon = document.getElementById('fan-icon');

    fanIcon.src = (fanStatus === 'ON' && fanSwitchRequested) ? ('/static/images/fan-on.webp') : ('/static/images/fan-off.webp');
    // TODO: ideally would display only the passed info
    // If not received yet, don't want to display "{{ fan_status }}"
    if (fanStatus === "{{ fan_status }}") {
        document.getElementById('fan-status').textContent = "Fan Status: OFF";
    } else {
        document.getElementById('fan-status').textContent = "Fan Status: " + fanStatus;
    }
}

function checkEmailNotification() {
    fetch('/check_email_notification')
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // If there's a notification, show a popup
                alert(data.message);
            }
        })
        .catch(error => console.error('Error checking email notification:', error));
}