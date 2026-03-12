// Identifying all Pins on the Arduino
const int mainPump     = 13; 
const int overflowPump = 12; 
const int lowLevel     = 7; 
const int highLevel    = 8; 

int lowState  = 0;
int highState = 0;

void setup() {
  Serial.begin(9600);

  pinMode(mainPump, OUTPUT);
  pinMode(overflowPump, OUTPUT);

  // IMPORTANT FIX — enable internal pull-ups
  pinMode(lowLevel, INPUT_PULLUP);
  pinMode(highLevel, INPUT_PULLUP);
}

void loop() {
  // Read switches (LOW = triggered, HIGH = not activated)
  lowState  = digitalRead(lowLevel);
  highState = digitalRead(highLevel);

  // Pump logic
  if (lowState == HIGH && highState == LOW) {
    digitalWrite(mainPump, HIGH);
    digitalWrite(overflowPump, HIGH);
  }
  else if (lowState == HIGH && highState == HIGH) {
    digitalWrite(mainPump, LOW);
    digitalWrite(overflowPump, HIGH);
  }
  else if (lowState == LOW && highState == LOW) {
    digitalWrite(mainPump, HIGH);
    digitalWrite(overflowPump, LOW);
  }
  else {
    digitalWrite(mainPump, LOW);
      digitalWrite(overflowPump, LOW);
  }

  // Read pump output states
  int mainPumpState     = digitalRead(mainPump);
  int overflowPumpState = digitalRead(overflowPump);

  // CSV output
  Serial.print(lowState);
  Serial.print(",");
  Serial.print(highState);
  Serial.print(",");
  Serial.print(mainPumpState);
  Serial.print(",");
  Serial.println(overflowPumpState);

  delay(200);
}
