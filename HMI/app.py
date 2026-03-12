import os
import csv
import time
from datetime import datetime, date

import serial
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

# ----------------- SENSOR ARDUINO -----------------
SENSOR_PORT = 'COM8'   # MKR WAN
SENSOR_BAUD = 9600

# ----------------- SERVO ARDUINO ------------------
SERVO_PORT = 'COM4'    # Uno (adjust if needed)
SERVO_BAUD = 9600

sensor_ser = serial.Serial(SENSOR_PORT, SENSOR_BAUD, timeout=1)
time.sleep(2)
print(f"Connected to sensor Arduino on {SENSOR_PORT} at {SENSOR_BAUD} baud")

servo_ser = serial.Serial(SERVO_PORT, SERVO_BAUD, timeout=1)
time.sleep(2)
print(f"Connected to servo Arduino on {SERVO_PORT} at {SERVO_BAUD} baud")

# ----------------- LOGGING SETUP ------------------

LOG_DIR = r"C:\Users\dazer\Documents\mcmaster\capstone-2\storedata"
os.makedirs(LOG_DIR, exist_ok=True)

_current_log_date = None
_log_file = None
_log_writer = None

#Returns a CSV writer for today's log file.
def get_log_writer():
  global _current_log_date, _log_file, _log_writer

  today = date.today()
  if _current_log_date != today:
    # rotate file
    if _log_file:
      _log_file.close()

    filename = os.path.join(LOG_DIR, f"sensors_{today.isoformat()}.csv")
    file_exists = os.path.exists(filename)
    _log_file = open(filename, "a", newline="")
    _log_writer = csv.writer(_log_file)

    if not file_exists:
      # write header once
      _log_writer.writerow(
        ["timestamp", "ambient_percent", "uv_percent", "temp_c", "flow_l_min"]
      )

    _current_log_date = today

  return _log_writer, _log_file

#log single data sample to CSV
def log_sample(data):
  writer, f = get_log_writer()
  ts = datetime.now().isoformat(timespec="seconds")
  writer.writerow([
    ts,
    data["ambient"],
    data["uv"],
    data["temp"],
    data["flow"],
  ])
  f.flush()


# ----------------- FLASK + SOCKETIO ---------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

background_thread = None


def sensor_reader_thread():
  """Background task: read Arduino and push data to all connected clients."""
  print("Sensor reader thread started")
  while True:
    try:
      line = sensor_ser.readline().decode(errors="ignore").strip()
      if not line:
        socketio.sleep(0.05)
        continue

      # Expected CSV: ambient,uv,temp,flow
      parts = line.split(",")
      if len(parts) != 4:
        print("Skipping bad line:", line)
        continue

      amb_str, uv_str, temp_str, flow_str = parts

      try:
        data = {
          "ambient": float(amb_str),
          "uv": float(uv_str),
          "temp": float(temp_str),
          "flow": float(flow_str),
        }
      except ValueError:
        print("Value error on line:", line)
        continue

      # --- log to CSV ---
      log_sample(data)

      # --- emit to HMI ---
      print("Emitting sensor_data:", data)
      socketio.emit("sensor_data", data)

      socketio.sleep(0.1)

    except Exception as e:
      print("Error in sensor_reader_thread:", e)
      socketio.sleep(1.0)


# ----------------- ROUTES -------------------------

@app.route("/")
def index():
  return render_template("index.html")


@app.route("/servo/feed", methods=["POST"])
def servo_feed():
  """HMI → Servo Arduino command."""
  try:
    servo_ser.write(b"F")
    servo_ser.flush()
    return jsonify({"status": "ok"})
  except Exception as e:
    print("Error sending feed command:", e)
    return jsonify({"status": "error", "error": str(e)}), 500


# ----------------- SOCKET.IO HANDLERS -------------

@socketio.on("connect")
def handle_connect():
  global background_thread
  print("Client connected")

  if background_thread is None:
    background_thread = socketio.start_background_task(sensor_reader_thread)


@socketio.on("disconnect")
def handle_disconnect():
  print("Client disconnected")


# ----------------- MAIN ---------------------------

if __name__ == "__main__":
  socketio.run(
    app,
    host="127.0.0.1",
    port=5000,
    debug=True,
    use_reloader=False,  # keep this so COM ports aren't opened twice
  )
