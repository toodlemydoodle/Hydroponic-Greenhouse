import time
import serial
from flask import Flask, jsonify, render_template

# ====== SERIAL CONFIG ======
PORT = 'COM3'      # change if needed
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # give Arduino time to reset

print(f"Connected to {PORT} at {BAUD} baud")

# If your Arduino prints a header first, read & discard it once:
# header = ser.readline().decode(errors='ignore').strip()
# print("Header from Arduino:", header)

app = Flask(__name__)


def read_values():
    """Read one valid CSV line from Arduino and return as dict."""
    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            continue

        parts = line.split(",")

        # Expecting: ambient,uv,temp,lowState,highState,flow
        if len(parts) != 6:
            print("Skipping bad line:", line)
            continue

        amb_str, uv_str, temp_str, lowS_str, highS_str, flow_str = parts

        try:
            data = {
                "ambient": float(amb_str),
                "uv": float(uv_str),
                "temp": float(temp_str),
                "lowState": int(lowS_str),
                "highState": int(highS_str),
                "flow": float(flow_str),
            }
            return data
        except ValueError:
            print("Value error on line:", line)
            continue


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    values = read_values()
    return jsonify(values)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)