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

function fetchData() {
    fetch('/sensor_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.temperature && data.humidity) {
                // Update text values for temperature and humidity [TO REMOVE IN LATER BUILD]
                document.getElementById('temp-value').textContent = data.temperature + '°C';
                document.getElementById('humidity-value').textContent = data.humidity + '%';


                // Update the gauge based on temperature
                tGauge.refresh(data.temperature);


                // Set humidity icon based on range
                const humidityIcon = document.getElementById('humidity-icon');
                if (data.humidity < 30) {
                    humidityIcon.src = '/static/images/humidity-low.webp';
                } else if (data.humidity <= 60) {
                    humidityIcon.src = '/static/images/humidity-mid.webp';
                } else {
                    humidityIcon.src = '/static/images/humidity-high.webp';
                }


                // Check if the fan should be toggled ON
                updateFan("{{ fan_status }}", "{{ fan_switch_requested }}");
            }
        })
        .catch(error => console.error('Error fetching sensor data:', error));
}

function initializeGauges() {
    let tGauge = new JustGage({
        id: "tgauge",
        value: -1,
        min: 15,
        max: 30,
        title: "Temperature"
      });
}


function updateLED(ledStatus) {
    const lightImage = document.getElementById('light-image');
    const toggleSwitch = document.getElementById('toggle-switch');


    toggleSwitch.checked = (ledStatus === 'ON');
    lightImage.src = (ledStatus === 'ON') ? ('/static/images/lit.png') : ('/static/images/dark.png');
    document.getElementById('led-status').textContent = "LED Status: " + ledStatus;
    lightImage.className = (ledStatus === 'ON') ? 'lit' : 'dark';
}


function updateFan(fanStatus, fanSwitchRequested) {
    const fanIcon = document.getElementById('fan-icon');


    fanIcon.src = (fanStatus === 'ON' && fanSwitchRequested) ? ('/static/images/fan-on.webp') : ('/static/images/fan-off.webp');
    document.getElementById('fan-status').textContent = "Fan Status: " + fanStatus;
}