from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from twilio.rest import Client

app = Flask(__name__)

# -------------------------------
# 🔐 TWILIO CONFIG (SAFE VERSION)
# -------------------------------
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_AUTH")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
USER_NUMBER = os.environ.get("USER_NUMBER")

client = Client(account_sid, auth_token)

# -------------------------------
# 📩 SMS FUNCTION
# -------------------------------
def send_sms(message):
    try:
        if not all([account_sid, auth_token, TWILIO_NUMBER, USER_NUMBER]):
            print("⚠️ Twilio credentials missing")
            return

        msg = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=USER_NUMBER
        )
        print("✅ SMS SENT:", msg.sid)

    except Exception as e:
        print("❌ SMS ERROR:", e)

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
# 📦 DATABASE SETUP
# -------------------------------
def init_db():
    conn = sqlite3.connect("gas.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  gas_level INTEGER,
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# 🌐 HOME (LOAD UI)
# -------------------------------
@app.route('/')
def home():
    return render_template("index.html")

# -------------------------------
# 🧯 GAS DETECTION (FIXED)
# -------------------------------
@app.route('/gas-data', methods=['POST'])
def gas_data():
    try:
        data = request.get_json()

        if not data or "gas_level" not in data:
            return jsonify({"error": "Invalid input"}), 400

        gas_level = int(data.get('gas_level'))

        print("📊 Gas Level:", gas_level)

        status = "ALERT" if gas_level > 300 else "SAFE"

        if status == "ALERT":
            appliances["main_power"] = "OFF"
            print("⚠️ GAS ALERT")
            send_sms("⚠️ GAS LEAK DETECTED! POWER CUT OFF!")

        # Save to DB
        conn = sqlite3.connect("gas.db")
        c = conn.cursor()
        c.execute("INSERT INTO readings (gas_level, status) VALUES (?, ?)",
                  (gas_level, status))
        conn.commit()
        conn.close()

        return jsonify({"status": status})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------
# 📊 GET DATA
# -------------------------------
@app.route('/data', methods=['GET'])
def get_data():
    conn = sqlite3.connect("gas.db")
    c = conn.cursor()
    c.execute("SELECT * FROM readings")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# -------------------------------
# ⚡ CONTROL APPLIANCES
# -------------------------------
@app.route('/control', methods=['POST'])
def control():
    try:
        data = request.get_json()

        device = data.get("device")
        action = data.get("action")

        if device in appliances:
            appliances[device] = action

            print(f"🔌 {device} → {action}")

            send_sms(f"{device.upper()} turned {action}")

            return jsonify({
                "status": "updated",
                "appliances": appliances
            })

        return jsonify({"error": "Invalid device"}), 400

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -------------------------------
# 🔍 GET APPLIANCES
# -------------------------------
@app.route('/appliances', methods=['GET'])
def get_appliances():
    return jsonify(appliances)

# -------------------------------
# 🔥 FIRE ALERT
# -------------------------------
@app.route('/fire', methods=['POST'])
def fire():
    try:
        print("🔥 FIRE DETECTED")

        appliances["main_power"] = "OFF"

        send_sms("🔥 FIRE DETECTED! POWER CUT OFF!")

        return jsonify({"status": "fire alert"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# 🧪 TEST SMS
# -------------------------------
@app.route('/test-sms')
def test_sms():
    send_sms("Test message from Smart Home")
    return "SMS Sent"

# -------------------------------
# ▶️ RUN SERVER (PRODUCTION SAFE)
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)