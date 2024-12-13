let temperatureGauge;
let humidityGauge;
let luminosityGauge;
let ledStatus = flaskData.ledStatus;
let fanStatus = flaskData.fanStatus;
let fanSwitchOn = flaskData.fanSwitchOn;
let fanSwitchOff = flaskData.fanSwitchOff;
let fanEmailSent = flaskData.fanEmailSent;
  
window.onload = () => {
    // Initialize everything first
    initializeGauges();
    fetchBluetoothDevices(); 
    
    document.getElementById('toggle-switch').addEventListener('change', function() {
        let newState = this.checked ? 'ON' : 'OFF';
        fetch(`/toggle_led/${newState}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => updateLED(data.led_status));
    });

    setInterval(() => {
        fetchStates(); // Setting the updated states from backend to the frontend | CALL THIS FIRST
        fetchData(); // DHT sensor data only, no effect on other variables
        fetchLightData(); // Photoresistor data only, no effect on other variables
        updateFan(); // Update UI and toggle backend
    }, 1000);

    setInterval(autoPopulateForm, 2000);
    updateLED(ledStatus);
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
        max: 5000,
        reverse: true,
        title: "Luminosity",
        gaugeWidthScale: 0.5,
        levelColors: ["#f7f697","#d1cfb6", "#2a2a2a"],
    });
}

function fetchData() {
    fetch('/sensor_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.temperature || data.temperature === 0) {
                // Update the gauges with values
                temperatureGauge.refresh(data.temperature);
            }
            if (data.humidity || data.humidity === 0) {
                // Update the gauges with values
                humidityGauge.refresh(data.humidity);
            }
        })
        .catch(error => console.error('Error fetching sensor data:', error));
}

function fetchLightData() {
    fetch('/light_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.luminosity || data.luminosity === 0) {
                // Update the gauges with values
                luminosityGauge.refresh(data.luminosity);
            }
        })
        .catch(error => console.error('Error fetching sensor data:', error));
}

function fetchStates() {
    fetch('/get_states')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.fanEmailSent) fanEmailSent = data.fanEmailSent;
            if (data.fanStatus) fanStatus = data.fanStatus;
            if (data.fanSwitchOn) fanSwitchOn = data.fanSwitchOn;
            if (data.fanSwitchOff) fanSwitchOff = data.fanSwitchOff;
            if (data.ledStatus) ledStatus = data.ledStatus;
        })
        .catch(error => console.error('Error fetching states:', error));
}

function updateLED(ledStatus) {
    // Defining the variables
    const lightImage = document.getElementById('light-image');
    const toggleSwitch = document.getElementById('toggle-switch');

    // Assigning the variables and displaying on the page
    toggleSwitch.checked = (ledStatus === 'ON');
    lightImage.src = (ledStatus === 'ON') ? ('/static/images/lit.png') : ('/static/images/dark.png');
    document.getElementById('led-status').textContent = "LED Status: " + ledStatus;
    lightImage.className = (ledStatus === 'ON') ? 'lit' : 'dark';
}


function updateFan() {
    fetch(`/toggle_fan/${fanStatus}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => fanStatus = data.fan_status);
    
    const fanIcon = document.getElementById('fan-icon');
    fanIcon.src = (fanStatus === 'ON' && fanSwitchOn) ? ('/static/images/fan-on.webp') : ('/static/images/fan-off.webp');
    document.getElementById('fan-status').textContent = "Fan Status: " + fanStatus;
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

// Function to fetch data and populate form fields
let currentRfid = localStorage.getItem('currentRfid') || "";
function autoPopulateForm() {
    fetch('/fetch_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        // Empty body to indicate no RFID tag was scanned
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error fetching user data:', data.error);
            alert('Could not load user data: ' + data.error);
        } else {
            // Populate form fields with fetched data
            if (currentRfid !== data.rfid_tag) {
                // Save the new RFID to localStorage before reloading
                localStorage.setItem('currentRfid', data.rfid_tag);
            } else {
                // Update currentRfid and store it
                currentRfid = data.rfid_tag;
                localStorage.setItem('currentRfid', currentRfid);
            }

            document.getElementById('rfid_tag').innerHTML = data.rfid_tag || '';
            document.getElementById('username').innerHTML = data.username || '';
            document.getElementById('email').innerHTML = data.email || '';
            document.getElementById('tempForm').value = data.temperature_threshold || '';
            document.getElementById('lightForm').value = data.lighting_intensity_threshold || '';
            
        }
        
    })
    .catch(error => {
        console.error('Error fetching user data:', error);
    });
}

let bluetoothDevices = []; // To hold all the Bluetooth devices
let currentIndex = 0; // To track the current set of devices to display

// Function to fetch Bluetooth devices from the Flask server
async function fetchBluetoothDevices() {
    try {
        const response = await fetch('/bluetooth_devices');
        bluetoothDevices = await response.json();

        if (bluetoothDevices.length > 0) {
            displayBluetoothDevices();
            updateDeviceCount(); // Update the device count when devices are fetched
        } else {
            const deviceList = document.getElementById('device-list');
            deviceList.innerHTML = '<li>No Bluetooth devices found.</li>';
            updateDeviceCount(); // Update the device count when no devices are found
        }
    } catch (error) {
        console.error('Error fetching Bluetooth devices:', error);
    }
}

// Function to display 4 devices at a time
function displayBluetoothDevices() {
    const deviceList = document.getElementById('device-list');
    deviceList.innerHTML = ''; // Clear the current list

    // Slice the bluetoothDevices array to get 4 devices starting from the current index
    const devicesToShow = bluetoothDevices.slice(currentIndex, currentIndex + 4);

    // Populate the list with the sliced devices
    devicesToShow.forEach(device => {
        const listItem = document.createElement('li');
        listItem.textContent = `Name: ${device.name}, Address: ${device.address}`;
        deviceList.appendChild(listItem);
    });
}

// Function to update the device count
function updateDeviceCount() {
    const deviceCountElement = document.getElementById('device-count');
    deviceCountElement.textContent = `Total Bluetooth Devices: ${bluetoothDevices.length}`;
}

// Function to cycle through the devices
function cycleDevices() {
    if (bluetoothDevices.length === 0) return; // No devices to cycle through

    // Move to the next set of 4 devices
    currentIndex = (currentIndex + 4) % bluetoothDevices.length;

    // If we are past the last set, we start from the beginning
    if (currentIndex >= bluetoothDevices.length) {
        currentIndex = 0;
    }

    displayBluetoothDevices();
}
