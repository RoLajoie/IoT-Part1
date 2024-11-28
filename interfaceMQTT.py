# import RPi.GPIO as GPIO
import mock_gpio as GPIO #MOCK: simulate GPIO
from gpiozero import DigitalOutputDevice
from flask import Flask, render_template, request, jsonify, redirect, url_for
import atexit
import paho.mqtt.client as mqtt
# from Freenove_DHT import DHT
from mock_dht import DHT #MOCK: simulates DHT
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import time
import ssl
from email.message import EmailMessage
import imaplib
import email
from email.header import decode_header
import sqlite3
from bluetooth_helper import BluetoothHelper # Importing hte bluetooth file 

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
#MQTT_BROKER = '192.168.101.131'
MQTT_BROKER = 'localhost' # MOCK: localhost :)
MQTT_TOPIC_LED = 'home/led'
MQTT_TOPIC_FAN = 'home/fan'
MQTT_TOPIC_LIGHT = 'home/light'
MQTT_TOPIC_RFID = 'home/rfid'
# State machines for fan and friends
led_state = 'OFF'
fan_state = 'OFF'
fan_switch_on = False
email_sent = False
# Dynamic Light Related Variables
light_intensity = 0
light_email_sent = False

current_user = {}  # Global variable to store the current user's data
current_rfid = '83adf703'; 
bt_helper = BluetoothHelper()
bluetooth_devices = bt_helper.get_bluetooth_devices()
# -------------------------------------------------------------------------------------------------------------------------->

# TODO: 
# Database implementation 
# When an new RFID tag shows up 
#

def start_bluetooth_scan():
    bt_helper.start_continuous_scan()

def init_db():
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    
    # Create the users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            rfid_tag TEXT UNIQUE NOT NULL,
            temperature_threshold INTEGER DEFAULT 24,
            light_intensity_threshold INTEGER DEFAULT 400
        )
    ''')
    
    # Insert default data
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, rfid_tag, temperature_threshold, light_intensity_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Maxim1', 'maximrotaru16@gmail.com', '83adf703', 24, 400))
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, rfid_tag, temperature_threshold, light_intensity_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Maxim2', 'lemonboysomething@gmail.com', 'a43a1051', 23, 500))
    
    conn.commit()
    conn.close()





# Retrieve user data
def get_user(rfid_tag):
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE rfid_tag = ?', (rfid_tag,))
    user = cursor.fetchone()
    conn.close()
    return user 


def update_user_preferences(rfid_tag, temp_threshold, light_threshold):
    conn = sqlite3.connect('smart_home.db')  # Use sqlite3.connect directly
    cursor = conn.cursor()
    
    # SQL query to update user preferences by RFID
    query = '''
    UPDATE users
    SET temperature_threshold = ?, light_intensity_threshold = ?
    WHERE rfid_tag = ?
    '''
    cursor.execute(query, (temp_threshold, light_threshold, rfid_tag))
    conn.commit()  # Commit the changes
    conn.close()


# -------------------------------------------------------------------------------------------------------------------------->

def send_email(temperature):
    global email_sent
    if not email_sent:
        msg = MIMEText(f"The current temperature is {temperature}°C. Would you like to turn on the fan?")
        msg['Subject'] = 'Temperature Alert'
        msg['From'] = 'whatisiot1@gmail.com' 
        msg['To'] = 'maximrotaru16@gmail.com' # MAKE DYNAMIC 
        # msg['To'] = 'levitind@gmail.com'

        
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

            # Search for all messages in the inbox
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()

            # Fetch and process each email
            for email_id in email_ids:
                # Decode email_id, since imaplib returns a byte string
                email_id = email_id.decode()

                res, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                # First we try to extract the body
                body = msg.get_payload(decode=True)

                # Next we check if body exists and decode it
                if body is None:
                    continue
                body = body.decode()

                # Check for "Yes" in the email body
                if "Yes" in body:
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
    global light_email_sent
    global current_user
    
    if not light_email_sent and 'email' in current_user:
        msg = MIMEText(f"Dark room detected. LED Light has been activated.")
        msg['Subject'] = 'LED Enabled'
        msg['From'] = 'whatisiot1@gmail.com'
        msg['To'] = current_user['email']  # Send email to the current user
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('whatisiot1@gmail.com', 'ayvi plyw mqzd vrtz')
                server.sendmail(msg['From'], [msg['To']], msg.as_string())
            print(f"Light activation email sent to {current_user['email']}")
            light_email_sent = True
        except Exception as e:
            print(f"Failed to send email: {e}")


# -------------------------------------------------------------------------------------------------------------------------->


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
    global light_intensity, light_email_sent, led_state, fan_state, fan_switch_on, email_sent, current_rfid

    if msg.topic == MQTT_TOPIC_LIGHT:
        try:
            light_intensity = int(msg.payload.decode())  # Decode and store the light intensity value
            print(f"Received light intensity: {light_intensity}")
            if light_intensity > 400 and not light_email_sent:
                led_state = 'ON'
                GPIO.output(LED_PIN, GPIO.HIGH)
                send_light_email()
                light_email_sent = True
            elif light_intensity <= 400:
                led_state = 'OFF'
                GPIO.output(LED_PIN, GPIO.LOW)
                light_email_sent = False
        except ValueError:
            print(f"Invalid light intensity value received: {msg.payload.decode()}")
    
    elif msg.topic == MQTT_TOPIC_RFID:
        try:
            rfid = msg.payload.decode()
            print(f"RFID Detected: {rfid}")
            current_rfid = rfid 
            # Fetch user details from the database
            user = get_user(rfid)
        
            if user:
                global current_user
                current_user = {
                    'rfid_tag': user[0],
                    'username': user[1],
                    'email': user[2],
                    'temp_threshold': user[4],
                    'light_threshold': user[5]
                }
            
                print(f"Switched to preferences for user: {current_user['username']}")
                
                # Notify the user via email
                notification_msg = f"""
                Hello {current_user['username']},
    
                Your preferences have been successfully activated at {time}:
                - Temperature Threshold: {current_user['temp_threshold']}°C
                - Light Intensity Threshold: {current_user['light_threshold']} lumens
    
                Thank you,
                Beep boop smart IoT system
                """
                send_email_to_user(current_user['email'], "Preferences Activated", notification_msg)
            else:
                print("No user found with this RFID tag.")
        except ValueError:
            print(f"Invalid RFID Value: {msg.payload.decode()}")



def send_email_to_user(to_email, subject, message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = 'whatisiot1@gmail.com'
        msg['To'] = to_email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('whatisiot1@gmail.com', 'ayvi plyw mqzd vrtz')
            server.sendmail(msg['From'], [to_email], msg.as_string())
        
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")




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
    global current_user
    while True:
        humidity, temperature = read_dht_sensor()
        if temperature is not None:
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            if temperature >= current_user["temperature_threshold"] and fan_state == 'OFF':
                if email_sent == False:
                    send_email(temperature)
                    email_sent = True
                    fan_state = "ON"
            elif temperature < current_user["temperature_threshold"] and fan_state == 'ON':
                fan_state = 'OFF'
                GPIO.output(FAN_PIN, GPIO.LOW)
        time.sleep(3)

# Start monitoring thread
Thread(target=monitor_temperature, daemon=True).start()
# Check email response thread
Thread(target=check_email_responses, daemon=True).start()
# Thread to do bluetooth
Thread(target=start_bluetooth_scan, daemon=True).start()

mqtt_client.on_message = on_message  # Attach the handler
mqtt_client.subscribe(MQTT_TOPIC_LIGHT)  # Subscribe to the light intensity topic
mqtt_client.subscribe(MQTT_TOPIC_RFID)

# Route to render the dashboard
@app.before_first_request
def setup():
    # Initialize the database
    init_db()
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()

@app.route('/')
def index():
    return render_template(
        'dashboard.html', 
        led_status=led_state, 
        fan_status=fan_state, 
        fan_switch_requested=fan_switch_on, 
        light_email_sent=light_email_sent, 
        devices=bluetooth_devices,
        current_user=current_user  # Pass the current_user object to the template
    )
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
    mqtt_client.publish(MQTT_TOPIC_RFID, 'OFF')

@app.route('/sensor_data')
def sensor_data():
    humidity, temperature = read_dht_sensor()  # Call your DHT sensor function
    if humidity is not None and temperature is not None:
        return jsonify({'temperature': temperature, 'humidity': humidity})
    else:
        return jsonify({'error': 'Could not retrieve sensor data'}), 500
    
@app.route('/light_data')
def light_data():
    if light_intensity is not None:
        return jsonify({'luminosity': light_intensity})
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

#------------------------------------------------------------------------------->

# Auto filling the form's information 
@app.route('/fetch_user', methods=['POST'])
def fetch_user():
    global current_user
    # For mock RFID
    # return jsonify({
    #         'id': '83adf703',
    #         'username': 'Maxim1',
    #         'email': 'maximrotaru16@gmail.com',
    #         'rfid_tag': '83adf703',
    #         'temperature_threshold': 24,  
    #         'lighting_intensity_threshold': 400,  
    # })
    
    ## THIS IS THE LINE THAT TRIES TO FIND RFID TAG GIVEN NEW INPUT 
    ## rfid_tag = current_user['rfid_tag']; 
    
    ## Line that populates currently 
    rfid_tag = request.json.get('rfid_tag')

    if current_rfid:
        rfid_tag = current_rfid
    
    if rfid_tag:
        current_user = get_user(rfid_tag)
    else:
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY id ASC LIMIT 1')
        currrent_user = cursor.fetchone()
        conn.close()
    
    if current_user:
        return jsonify({
            'id': current_user[0],
            'username': current_user[1],
            'email': current_user[2],
            'rfid_tag': current_user[3],
            'temperature_threshold': current_user[4],  
            'lighting_intensity_threshold': current_user[5],  
        })
    else:
        return jsonify({'error': 'No users found in the database'}), 404

@app.route('/add_or_update_user', methods=['POST'])
def add_or_update_user():
    username = request.form.get('username')
    email = request.form.get('email')
    rfid_tag = request.form.get('rfid_tag')
    temp_threshold = request.form.get('tempForm')
    light_threshold = request.form.get('lightForm')
    
    if not all([username, email, rfid_tag, temp_threshold, light_threshold]):
        return jsonify({"error": "All fields are required"}), 400

    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE rfid_tag = ?', (rfid_tag,))
    user = cursor.fetchone()

    if user:
        # Update existing user
        cursor.execute('''
            UPDATE users
            SET username = ?, email = ?, temperature_threshold = ?, light_intensity_threshold = ?
            WHERE rfid_tag = ?
        ''', (username, email, temp_threshold, light_threshold, rfid_tag))
    else:
        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, email, rfid_tag, temperature_threshold, light_intensity_threshold)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, rfid_tag, temp_threshold, light_threshold))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# Flask Route to serve Bluetooth devices
@app.route('/bluetooth_devices')
def bluetooth_devices_list():
    return jsonify(bluetooth_devices)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
