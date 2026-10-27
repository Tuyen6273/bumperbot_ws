#include <Arduino.h>
#define LED_PIN 13


void setup() {
  // put your setup code here, to run once:
  pinMode(LED_PIN, 13);
  digitalWrite(13, LOW);

  Serial.begin(115200);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()){
    int x = Serial.readString().toInt();
    if(x == 0){
      digitalWrite(LED_PIN, LOW);
      Serial.println("Turn off the led");
    } 
    else{
      digitalWrite(LED_PIN, HIGH);
      Serial.println("Turn on the led");
    }
  }
}
