import RPi.GPIO as GPIO
from gpiozero import DigitalOutputDevice
from flask import Flask, render_template, request, jsonify
import atexit
import paho.mqtt.client as mqtt
from Freenove_DHT import DHT
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import time

# Define pin assignments
LED_PIN = 12    # LED control pin
FAN_PIN = 18    # Fan (DC motor) control pin
DHT_PIN = 6     # DHT-11 sensor pin

# Set up GPIO for LED and Fan
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT)

# Turn off LED and fan by default
GPIO.output(LED_PIN, GPIO.LOW)
GPIO.output(FAN_PIN, GPIO.LOW)

# Initialize DHT sensor
dht_sensor = DHT(DHT_PIN)

# MQTT configuration
MQTT_BROKER = 'localhost'  # Replace with broker IP if needed
MQTT_TOPIC = 'home/led'
led_state = 'OFF'
fan_state = 'OFF'

# Define email function for temperature alerts
def send_email(temperature):
    msg = MIMEText(f"The current temperature is {temperature}°C. Would you like to turn on the fan?")
    msg['Subject'] = 'Temperature Alert'
    msg['From'] = 'your_email@example.com'
    msg['To'] = 'recipient_email@example.com'
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'your_password')
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
    print('Email sent')

# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Flask setup
app = Flask(__name__)

# Sensor reading functionTemperature: 24.0°C, Humidity: 44.0%

def read_dht_sensor():
    chk = dht_sensor.readDHT11()
    if chk == 0:  # 0 indicates successful read
        humidity = dht_sensor.getHumidity()
        temperature = dht_sensor.getTemperature()
        return humidity, temperature
    else:
        print("Failed to retrieve data from DHT sensor")
        return None, None


# Function to monitor temperature and control fan
def monitor_temperature():
    global fan_state
    while True:
        humidity, temperature = read_dht_sensor()
        if temperature is not None:
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            if temperature > 24:
                send_email(temperature)
                fan_state = 'ON'
                GPIO.output(FAN_PIN, GPIO.HIGH)
            else:
                fan_state = 'OFF'
                GPIO.output(FAN_PIN, GPIO.LOW)
        time.sleep(10)

# Start monitoring thread
Thread(target=monitor_temperature, daemon=True).start()

# Route to render the dashboard
@app.route('/')
def index():
    return render_template('dashboardMQTT.html', led_status=led_state, fan_status=fan_state)

# Route to toggle LED via MQTT
@app.route('/toggle_led/<state>', methods=['POST'])
def toggle_led(state):
    global led_state
    led_state = state
    mqtt_client.publish(MQTT_TOPIC, state)
    GPIO.output(LED_PIN, GPIO.HIGH if state == 'ON' else GPIO.LOW)
    return jsonify({'led_status': state}), 200

# Route to control fan directly
@app.route('/toggle_fan/<state>', methods=['POST'])
def toggle_fan(state):
    global fan_state
    fan_state = state
    GPIO.output(FAN_PIN, GPIO.HIGH if state == 'ON' else GPIO.LOW)
    return jsonify({'fan_status': state}), 200

# Handle app exit to ensure GPIO is cleaned up
def on_exit():
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(FAN_PIN, GPIO.LOW)
    GPIO.cleanup()

@app.route('/sensor_data')
def sensor_data():
    humidity, temperature = read_dht_sensor()  # Call your DHT sensor function
    if humidity is not None and temperature is not None:
        return jsonify({'temperature': temperature, 'humidity': humidity})
    else:
        return jsonify({'error': 'Could not retrieve sensor data'}), 500


atexit.register(on_exit)

if __name__ == '__main__':
    app.run(debug=True)
