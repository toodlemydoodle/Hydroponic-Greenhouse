#include <Servo.h>

Servo myServo;

void setup() {
  Serial.begin(9600);
  myServo.attach(9);
  myServo.write(0); // start position
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();

    if (c == 'F') {
      sweepForFiveSeconds();
      Serial.println("FED");
    }
  }
}

void sweepForFiveSeconds() {
  unsigned long startTime = millis();

  while (millis() - startTime < 5000) {  // run for 5 seconds
    // Sweep 0 → 180
    for (int pos = 0; pos <= 180; pos++) {
      myServo.write(pos);
      delay(5);  // adjust speed here
      if (millis() - startTime >= 5000) return;
    }

    // Sweep 180 → 0
    for (int pos = 180; pos >= 0; pos--) {
      myServo.write(pos);
      delay(5);  // adjust speed here
      if (millis() - startTime >= 5000) return;
    }
  }

  // After 5 sec → return to rest
  myServo.write(0);
}
