from flask import Flask, render_template, jsonify, Response
import cv2
import numpy as np

app = Flask(__name__)

# Appliance states
appliances = {
    "fan": False,
    "tv": False,
    "ac": False,
    "washing_machine": False,
    "fridge": False
}

gas_detected = False

# Camera
camera = cv2.VideoCapture(0)

def generate_frames():
    global gas_detected

    while True:
        success, frame = camera.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Simulated gas detection
        if np.mean(gray) > 200:
            gas_detected = True
            for device in appliances:
                appliances[device] = False

            cv2.putText(frame, "GAS DETECTED!", (50,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    return render_template('index.html', appliances=appliances, gas=gas_detected)

@app.route('/toggle/<device>')
def toggle(device):
    appliances[device] = not appliances[device]
    return jsonify(appliances)

@app.route('/gas')
def gas():
    global gas_detected
    gas_detected = not gas_detected

    if gas_detected:
        for device in appliances:
            appliances[device] = False

    return jsonify({"gas": gas_detected})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run()