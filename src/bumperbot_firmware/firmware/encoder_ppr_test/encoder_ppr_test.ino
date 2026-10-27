#include <Arduino.h>

// Giu nguyen cac chan encoder va enable trong code dieu khien.
constexpr uint8_t RIGHT_ENCODER_A = 18;
constexpr uint8_t LEFT_ENCODER_A = 23;
constexpr uint8_t RIGHT_MOTOR_ENABLE = 14;
constexpr uint8_t LEFT_MOTOR_ENABLE = 12;

volatile uint32_t right_pulses = 0;
volatile uint32_t left_pulses = 0;
volatile bool measuring = false;
portMUX_TYPE encoder_mux = portMUX_INITIALIZER_UNLOCKED;

void ARDUINO_ISR_ATTR rightEncoderCallback() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  if (measuring) right_pulses++;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void ARDUINO_ISR_ATTR leftEncoderCallback() {
  portENTER_CRITICAL_ISR(&encoder_mux);
  if (measuring) left_pulses++;
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void setup() {
  // Tat enable L298N de xoay truc bang tay, khong chay PID.
  pinMode(RIGHT_MOTOR_ENABLE, OUTPUT);
  pinMode(LEFT_MOTOR_ENABLE, OUTPUT);
  digitalWrite(RIGHT_MOTOR_ENABLE, LOW);
  digitalWrite(LEFT_MOTOR_ENABLE, LOW);

  pinMode(RIGHT_ENCODER_A, INPUT);
  pinMode(LEFT_ENCODER_A, INPUT);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENCODER_A),
                  rightEncoderCallback, RISING);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENCODER_A),
                  leftEncoderCallback, RISING);

  Serial.begin(115200);
  Serial.println("\nDO XUNG ENCODER - pha A, RISING (x1)");
  Serial.println("Gui r: reset va bat dau dem.");
  Serial.println("Xoay truc dung 1 vong theo mot chieu.");
  Serial.println("Gui s: dung dem va in ket qua.");
}

void loop() {
  if (!Serial.available()) return;
  char command = Serial.read();

  if (command == 'r' || command == 'R') {
    portENTER_CRITICAL(&encoder_mux);
    right_pulses = 0;
    left_pulses = 0;
    measuring = true;
    portEXIT_CRITICAL(&encoder_mux);
    Serial.println("Da ve 0. Hay xoay truc dung 1 vong, sau do gui s.");
  } else if (command == 's' || command == 'S') {
    uint32_t right, left;
    portENTER_CRITICAL(&encoder_mux);
    measuring = false;
    right = right_pulses;
    left = left_pulses;
    portEXIT_CRITICAL(&encoder_mux);

    Serial.print("Phai: ");
    Serial.print(right);
    Serial.print(" xung | Trai: ");
    Serial.print(left);
    Serial.println(" xung");
    Serial.println("Gui r de do lai.");
  }
}
