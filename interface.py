import RPi.GPIO as GPIO
from flask import Flask, request, jsonify, render_template
import atexit

# pip install flask

# HOW TO RUN (go to cmd and type): python interface.py

app = Flask(__name__)
LED_PIN = 12 # pin num
led_state = 'OFF'
#config
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

#runs the function when its shutting down
def on_exit():
    GPIO.output(LED_PIN, GPIO.LOW)

#remembers to call the function at exit
atexit.register(on_exit)

@app.route('/')
def index():
    global led_state
    #passing LED state to the HTML template for syncing led and dashboard always
    return render_template('dashboard.html', led_status=led_state)

@app.route('/toggle_led', methods=['POST'])
def toggle_led():
    global led_state
    data = request.get_json()
    new_state = data.get('state')
    print(f"Received LED state: {new_state}")

    #update the physical LED 
    if new_state == 'ON':
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("Physical LED turned ON")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        print("Physical LED turned OFF")

    #update state variable
    led_state = new_state

    #new state returned as a JSON response
    return jsonify({'led_status': new_state}), 200

if __name__ == '__main__':
    #checks if flask is being exited
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("Exiting...")
