from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import cv2
import numpy as np
from twilio.rest import Client

app = Flask(__name__)

# -------------------------------
# 🔐 TWILIO CONFIG
# -------------------------------

account_sid = "AC20387d7cd6a0d901ba30fdb4362aa0fa"
auth_token = "4d504fc630520eb39197cbf53f5ff063"

TWILIO_NUMBER = "+19785414309"
USER_NUMBER = "+919791265620"

client = Client(account_sid, auth_token)

def send_sms(msg):
    try:
        client.messages.create(body=msg, from_=TWILIO_NUMBER, to=USER_NUMBER)
        print("SMS Sent")
    except Exception as e:
        print("SMS Error:", e)

# -------------------------------
# 📦 DATABASE
# -------------------------------
def init_db():
    conn = sqlite3.connect("gas.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  gas_level TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# 🏠 APPLIANCES
# -------------------------------
appliances = {
    "fan": "OFF",
    "tv": "OFF",
    "ac": "OFF",
    "light": "OFF",
    "fridge": "ON",
    "washing_machine": "OFF",
    "main_power": "ON"
}

# -------------------------------
# 🌐 HOME
# -------------------------------
@app.route('/')
def home():
    return render_template("index.html")

# -------------------------------
# 🧯 GAS DETECTION
# -------------------------------
@app.route('/gas-data', methods=['POST'])
def gas_data():
    try:
        data = request.get_json()
        gas_level = int(data.get("gas_level"))

        status = "ALERT" if gas_level > 300 else "SAFE"

        if status == "ALERT":
            appliances["main_power"] = "OFF"
            send_sms("⚠️ GAS LEAK DETECTED!")

        conn = sqlite3.connect("gas.db")
        c = conn.cursor()
        c.execute("INSERT INTO readings (gas_level, status) VALUES (?, ?)",
                  (gas_level, status))
        conn.commit()
        conn.close()

        return jsonify({"status": status})

    except Exception as e:
        return jsonify({"status": "ERROR", "msg": str(e)})

# -------------------------------
# 🎥 VIDEO DETECTION
# -------------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    try:
        file = request.files['video']
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        cap = cv2.VideoCapture(path)
        detected = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower = np.array([0, 120, 150])
            upper = np.array([35, 255, 255])

            mask = cv2.inRange(hsv, lower, upper)

            ratio = cv2.countNonZero(mask) / (frame.size)

            if ratio > 0.02:
                detected = True
                break

        cap.release()

        result = "DETECTED" if detected else "SAFE"

        conn = sqlite3.connect("gas.db")
        c = conn.cursor()
        c.execute("INSERT INTO readings (gas_level, status) VALUES (?, ?)",
                  ("VIDEO", result))
        conn.commit()
        conn.close()

        if detected:
            appliances["main_power"] = "OFF"
            send_sms("🔥 FIRE DETECTED!")

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"result": "ERROR", "msg": str(e)})

# -------------------------------
# ⚡ CONTROL
# -------------------------------
@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    device = data['device']
    action = data['action']

    appliances[device] = action
    return jsonify(appliances)

# -------------------------------
# 📊 VIEW DATABASE
# -------------------------------
@app.route('/view-data')
def view_data():
    conn = sqlite3.connect("gas.db")
    c = conn.cursor()
    c.execute("SELECT * FROM readings")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# -------------------------------
# ▶️ RUN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
