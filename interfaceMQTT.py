# import RPi.GPIO as GPIO
import mock_gpio as GPIO #MOCK: simulate GPIO
from gpiozero import DigitalOutputDevice
from flask import Flask, render_template, request, jsonify
import atexit
import paho.mqtt.client as mqtt
from Freenove_DHT import DHT
# from mock_dht import DHT #MOCK: simulates DHT
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import time
import ssl
from email.message import EmailMessage
import imaplib
import email
from email.header import decode_header

# Define pin assignments
LED_PIN = 12    # LED control pin
FAN_POWER_PIN = 18    # Fan (DC motor) control pin
FAN_PIN = 26    # Fan (DC motor) control pin
DHT_PIN = 13     # DHT-11 sensor pin

GPIO.setwarnings(False) #disable warnings
# Set up GPIO for LED and Fan
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.setup(FAN_POWER_PIN, GPIO.OUT)

# Turn off LED and fan by default

GPIO.output(LED_PIN, GPIO.LOW)
GPIO.output(FAN_PIN, GPIO.LOW)
GPIO.output(FAN_POWER_PIN, GPIO.HIGH)


# Initialize DHT sensor
dht_sensor = DHT(DHT_PIN)


# MQTT configuration
MQTT_BROKER = '192.168.55.131'
# MQTT_BROKER = 'localhost' # MOCK: localhost :)
MQTT_TOPIC_LED = 'home/led'
MQTT_TOPIC_FAN = 'home/fan'
MQTT_TOPIC_LIGHT = 'home/light'
# State machines for fan and friends
led_state = 'OFF'
fan_state = 'OFF'
fan_switch_on = False
email_sent = False
# Dynamic Light Related Variables
light_intensity = 0
light_email_sent = False; 

def send_email(temperature):
    global email_sent
    if not email_sent:
        msg = MIMEText(f"The current temperature is {temperature}°C. Would you like to turn on the fan?")
        msg['Subject'] = 'Temperature Alert'
        msg['From'] = 'whatisiot1@gmail.com'
        # msg['To'] = 'maximrotaru16@gmail.com'
        msg['To'] = 'levitind@gmail.com'

        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('whatisiot1@gmail.com', 'ayvi plyw mqzd vrtz')
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        email_sent = True
        print('Email sent')

def check_email_responses():
    global fan_switch_on
    while True:
        try:
            
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(username, imap_password)
            mail.select("inbox")

            # For email respond in the subject 
            status, messages = mail.search(None, 'SUBJECT "Re:"')
            email_ids = messages[0].split()

            # Fetch and process each reply
            for email_id in email_ids:
                res, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                # Check for "Yes" in the subject
                if "Yes" in subject:
                    print("Yes detected in response, activating FAN")
                    mail.store(email_id, '+FLAGS', '\\Deleted')
                    mail.expunge()
                    GPIO.output(FAN_PIN, GPIO.HIGH)
                    fan_switch_on = True

           
            mail.logout()
            time.sleep(10)  

        except Exception as e:
            print(f"Error checking emails: {e}")

def send_light_email():
    global email_sent
    if not email_sent:
        msg = MIMEText(f"Dark room detected. LED Light has been activated")
        msg['Subject'] = 'LED Enabled'
        msg['From'] = 'whatisiot1@gmail.com'
        # msg['To'] = 'maximrotaru16@gmail.com'
        msg['To'] = 'rowanlajoie04@gmail.com'

        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('whatisiot1@gmail.com', 'ayvi plyw mqzd vrtz')
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        email_sent = True
        print('Email sent')



# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Email configuration for sending alerts
port = 465
app_specific_password = "ayvi plyw mqzd vrtz"

# Email configuration for checking responses
username = "whatisiot1@gmail.com"
imap_password = "ayvi plyw mqzd vrtz"

# Flask setup
app = Flask(__name__)

def on_message(client, userdata, msg):
    global light_intensity
    if msg.topic == MQTT_TOPIC_LIGHT:
        try:
            light_intensity = int(msg.payload.decode())  # Decode and store the light intensity value
            print(f"Received light intensity: {light_intensity}")
            if light_intensity < 400 and not light_email_sent:
                toggle_led('ON')
                send_light_email()
                light_email_sent = True  # Set flag to true after sending the email

            # Reset the flag if light intensity is back above the threshold
            elif light_intensity >= 400:
                light_email_sent = False
        except ValueError:
            print(f"Invalid light intensity value received: {msg.payload.decode()}")


def read_dht_sensor():
    chk = dht_sensor.readDHT11()
    if chk == 0:  # 0 indicates successful read
        humidity = dht_sensor.getHumidity()
        temperature = dht_sensor.getTemperature()
        return humidity, temperature
    else:
        #PRINT THIS IF NEEDED
        #print("Failed to retrieve data from DHT sensor")
        return None, None


# Function to monitor temperature and control fan
def monitor_temperature():
    global fan_state
    global email_sent
    while True:
        humidity, temperature = read_dht_sensor()
        if temperature is not None:
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            if temperature >= 24 and fan_state == 'OFF':
                if email_sent == False:
                    send_email(temperature)
                    email_sent = True
                    fan_state = "ON"
            elif temperature < 24 and fan_state == 'ON':
                fan_state = 'OFF'
                GPIO.output(FAN_PIN, GPIO.LOW)
        time.sleep(3)

# Start monitoring thread
Thread(target=monitor_temperature, daemon=True).start()
# Check email response thread
Thread(target=check_email_responses, daemon=True).start()

mqtt_client.on_message = on_message  # Attach the handler
mqtt_client.subscribe(MQTT_TOPIC_LIGHT)  # Subscribe to the light intensity topic

# Route to render the dashboard
@app.route('/')
def index():
    return render_template('dashboard.html', led_status=led_state, fan_status=fan_state, fan_switch_requested=fan_switch_on, luminosity=light_intensity, light_email_sent = light_email_sent)

# Route to toggle LED via MQTT
@app.route('/toggle_led/<state>', methods=['POST'])
def toggle_led(state):
    global led_state
    led_state = state
    print(f"LED state set to: {led_state}") # Debugging purposes
    mqtt_client.publish(MQTT_TOPIC_LED, led_state)
    GPIO.output(LED_PIN, GPIO.HIGH if led_state == 'ON' else GPIO.LOW)
    return jsonify({'led_status': led_state}), 200

# Route to control fan via MQTT
@app.route('/toggle_fan/<state>', methods=['POST'])
def toggle_fan(state):
    global fan_state
    fan_state = state
    print(f"Fan state set to: {fan_state}") # Debugging purposes
    mqtt_client.publish(MQTT_TOPIC_FAN, fan_state)
    GPIO.output(FAN_PIN, GPIO.HIGH if fan_state == 'ON' else GPIO.LOW)
    return jsonify({'fan_status': fan_state}), 200

# Handle app exit to ensure GPIO is cleaned up
def on_exit():
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(FAN_PIN, GPIO.LOW)
    GPIO.cleanup()
    mqtt_client.publish(MQTT_TOPIC_LED, 'OFF')
    mqtt_client.publish(MQTT_TOPIC_FAN, 'OFF')

@app.route('/sensor_data')
def sensor_data():
    humidity, temperature = read_dht_sensor()  # Call your DHT sensor function
    if humidity is not None and temperature is not None:
        return jsonify({'temperature': temperature, 'humidity': humidity})
    else:
        return jsonify({'error': 'Could not retrieve sensor data'}), 500


# Checking the email has been sent for the light
@app.route('/check_email_notification')
def check_email_notification():
    global light_email_sent
    if light_email_sent:
        # Reset the notification flag to avoid repeated alerts
        light_email_sent = False
        return jsonify({'message': 'Light Notification Has Been Sent.'}), 200
    else:
        return jsonify({'message': None}), 200


atexit.register(on_exit)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
