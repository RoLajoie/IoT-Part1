import RPi.GPIO as GPIO
from flask import Flask, request, jsonify, render_template

# pip install flask

# HOW TO RUN (go to cmd and type): python interface.py

# All information that is useful to debug will be in [Inspect Element -> Console]

app = Flask(__name__)
LED_PIN = 12 # pin num
#config
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

@app.route('/')
def index():
    new_state = "OFF"
    return render_template('dashboard.html')

@app.route('/toggle_led', methods=['POST'])
def toggle_led():
    data = request.get_json()
    new_state = data.get('state')
    print("Received LED state: {new_state}")
    if new_state == 'ON':
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("Physical LED turned ON")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        print("Physical LED turned OFF")

    #sending LED state to update the web page with the 200 status code
    return jsonify({'led_status': new_state}), 200



if __name__ == '__main__':
    app.run(debug=True)
