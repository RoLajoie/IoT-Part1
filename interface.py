##import RPi.GPIO as GPIO 

from flask import Flask, request, jsonify, render_template

# pip install flask 

# HOW TO RUN (go to cmd and type): python interface.py 

# All information that is useful to debug will be in [Inspect Element -> Console] 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/toggle_led', methods=['POST']) 
def toggle_led():
    data = request.get_json()
    new_state = data.get('state')

    print("Received LED state: {new_state}")

    control_physical_led(new_state)

    #sending LED state to update the web page with the 200 status code
    return jsonify({'led_status': new_state}), 200

def control_physical_led(state):

    LED_PIN = 69 # pin num  
    #config 
    ##GPIO.setmode(GPIO.BCM) 
    ##GPIO.setup(LED_PIN, GPIO.OUT)

    if state == 'ON':
        ##GPIO.output(LED_PIN, GPIO.HIGH)
        print("Physical LED turned ON")
    else:
        ##GPIO.output(LED_PIN, GPIO.LOW) 
        print("Physical LED turned OFF")

    ##GPIO.cleanup()

if __name__ == '__main__':
    app.run(debug=True)
