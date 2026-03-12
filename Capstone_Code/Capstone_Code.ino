#include <math.h>

// --- Pins ---
const int uvLight      = A0;   // Sunshine UV sensor (0–3.3 V only)
const int ambientLight = A1;   // Ambient light sensor (0–3.3 V only)
const int ambientTemp  = A2;   // Thermistor divider (0–3.3 V only)
const int flowSensor   = 9;    // Flow sensor (open collector to GND, use pull-up)

// --- Constants ---
const float aMax          = 1023.0;   // max ADC count
const float supplyVoltage = 3.3;      // MKR WAN analog reference
const float Rfixed        = 4700.0;   // fixed resistor in thermistor divider
const float Beta          = 3950.0;   // B-value of thermistor
const float R0            = 10000.0;  // thermistor resistance at T0
const float T0            = 25.0 + 273.15; // K

void setup() {
  Serial.begin(9600);

  // For SAMD boards: wait for Serial to come up when USB connected
  while (!Serial) {
    ; // wait
  }

  pinMode(flowSensor, INPUT_PULLUP);  // assumes sensor pulls LOW when pulsing
}

void loop() {
  // --- Read sensors ---
  float amb  = ambientLightP();
  float uv   = uvP();
  float temp = temperature();
  float flow = flowValue();

  // --- Send CSV line: ambient,uv,temp,flow ---
  Serial.print(amb);   Serial.print(',');
  Serial.print(uv);    Serial.print(',');
  Serial.print(temp);  Serial.print(',');
  Serial.println(flow);

  delay(200); // 5 Hz
}

// --- Analog Sensors ---

float ambientLightP() {
  // percentage of full scale
  float raw = (float)analogRead(ambientLight);
  return (raw * 100.0) / aMax;
}

float uvP() {
  float raw = (float)analogRead(uvLight);
  return (raw * 100.0) / aMax;
}

float temperature() {
  float val = (float)analogRead(ambientTemp);

  // voltage at the divider node
  float v = (val * supplyVoltage) / aMax;  // 0–3.3 V

  // protect against division-by-zero if v is 0
  if (v <= 0.0001) {
    return NAN;
  }

  // assuming thermistor is on top and Rfixed to GND,
  // and we measure Vout at their junction
  float Rtherm = (supplyVoltage - v) * Rfixed / v;

  // protect against bad resistance before log()
  if (Rtherm <= 0) {
    return NAN;
  }

  // Beta-equation version of Steinhart–Hart
  float invT = (1.0 / T0) + (1.0 / Beta) * log(Rtherm / R0);
  float T    = (1.0 / invT) - 273.15; // °C

  return T;
}

// --- Flow Sensor ---

float flowValue() {
  const unsigned long timeout = 1000000UL; // 1 s timeout

  // High and low pulse durations (microseconds)
  unsigned long dHigh = pulseIn(flowSensor, HIGH, timeout);
  unsigned long dLow  = pulseIn(flowSensor, LOW,  timeout);

  if (dHigh == 0 || dLow == 0) {
    // no pulses in timeout window -> treat as 0 flow
    return 0.0;
  }

  unsigned long flowPeriod = dHigh + dLow;         // total period in µs
  float flowF = 1000000.0 / (float)flowPeriod;     // Hz

  //7.5 Hz per L/min
  return flowF / 7.5;  // L/min
}