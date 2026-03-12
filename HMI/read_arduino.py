import serial

# Open COM3 at 9600 baud
ser = serial.Serial('COM3', 9600)

print("Connected to Arduino on COM3")
print("Reading data...\n")

while True:
    line = ser.readline().decode().strip()
    parts = line.split(",")

    if len(parts) == 6:
        amb, uv, temp, lowS, highS, flow = parts

        print(f"Ambient: {amb}%   UV: {uv}%   Temp: {temp}°C   "
              f"Low: {lowS}   High: {highS}   Flow: {flow} L/min")
