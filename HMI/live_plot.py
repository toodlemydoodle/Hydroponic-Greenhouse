import serial
import time
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ==== CONFIGURATION ====
PORT = 'COM3'       # Change if your Arduino is on a different COM port
BAUD = 9600
MAX_POINTS = 200    # Number of points to keep on the graph

# ==== OPEN SERIAL PORT ====
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # Wait a bit for Arduino reset

print(f"Connected to {PORT} at {BAUD} baud.")

# If your Arduino prints a header line like:
#   ambient,uv,temp,lowState,highState,flow
# this will read and discard it
first_line = ser.readline().decode(errors='ignore').strip()
print("First line from Arduino:", first_line)

# ==== DATA BUFFERS ====
x_data   = deque(maxlen=MAX_POINTS)  # sample index
amb_data = deque(maxlen=MAX_POINTS)  # ambient light %
uv_data  = deque(maxlen=MAX_POINTS)  # UV %
temp_data= deque(maxlen=MAX_POINTS)  # temperature °C
flow_data= deque(maxlen=MAX_POINTS)  # flow

index = 0

# ==== MATPLOTLIB SETUP ====
plt.ion()
fig, ax = plt.subplots()

line_amb,  = ax.plot([], [], label="Ambient %")
line_uv,   = ax.plot([], [], label="UV %")
line_temp, = ax.plot([], [], label="Temp °C")
line_flow, = ax.plot([], [], label="Flow")

ax.set_xlabel("Sample")
ax.set_ylabel("Value")
ax.set_title("Live Arduino Sensor Data")
ax.legend(loc="upper left")
ax.grid(True)

# ==== UPDATE FUNCTION ====
def update(frame):
    global index

    try:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            return line_amb, line_uv, line_temp, line_flow

        parts = line.split(",")

        # Expecting 6 values: ambient,uv,temp,lowState,highState,flow
        if len(parts) != 6:
            # Could be header or a malformed line -> skip
            print("Skipping line:", line)
            return line_amb, line_uv, line_temp, line_flow

        amb_str, uv_str, temp_str, lowS_str, highS_str, flow_str = parts

        amb  = float(amb_str)
        uv   = float(uv_str)
        temp = float(temp_str)
        flow = float(flow_str)

        # Append new data
        x_data.append(index)
        amb_data.append(amb)
        uv_data.append(uv)
        temp_data.append(temp)
        flow_data.append(flow)
        index += 1

        # Update data for each line
        line_amb.set_data(x_data, amb_data)
        line_uv.set_data(x_data, uv_data)
        line_temp.set_data(x_data, temp_data)
        line_flow.set_data(x_data, flow_data)

        # Adjust axes
        ax.relim()
        ax.autoscale_view()

    except ValueError:
        # Could not convert to float – ignore that line
        print("ValueError on line:", line)
    except UnicodeDecodeError:
        # Weird serial noise – ignore
        pass

    return line_amb, line_uv, line_temp, line_flow

# ==== ANIMATION ====
ani = animation.FuncAnimation(
    fig,
    update,
    interval=200,   # match your Arduino delay(200)
    blit=False
)

print("Starting live plot. Close the window to stop.")
plt.show()

# When the plot window is closed:
ser.close()
print("Serial port closed.")