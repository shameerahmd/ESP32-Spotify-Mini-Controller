#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("ESP32 Spotify Controller");
    Serial.println("Firmware started successfully");
}

void loop() {
    delay(1000);
}