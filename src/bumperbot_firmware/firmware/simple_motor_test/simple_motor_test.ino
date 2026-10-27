/*
 * Code test 2 động cơ chạy tiến (Forward) cho ESP32 và mạch cầu H L298N
 * Vị trí: bumperbot_firmware/firmware/simple_motor_test/simple_motor_test.ino
 */

// Chân điều khiển ĐỘNG CƠ PHẢI (Motor A)
#define L298N_enA  14
#define L298N_in1  26
#define L298N_in2  27

// Chân điều khiển ĐỘNG CƠ TRÁI (Motor B)
#define L298N_enB  12
#define L298N_in3  25
#define L298N_in4  24

// Tốc độ quay (PWM từ 0 - 255), đặt 180 để chạy vừa phải an toàn
#define MOTOR_SPEED 180

void setup() {
    Serial.begin(115200);
    Serial.println("=== KHOI DONG TEST DONG CO ESP32 ===");

    // Cấu hình tất cả các chân điều khiển là OUTPUT
    pinMode(L298N_enA, OUTPUT);
    pinMode(L298N_in1, OUTPUT);
    pinMode(L298N_in2, OUTPUT);

    pinMode(L298N_enB, OUTPUT);
    pinMode(L298N_in3, OUTPUT);
    pinMode(L298N_in4, OUTPUT);

    // 1. Đặt chiều quay TIẾN (Forward)
    // Bánh phải
    digitalWrite(L298N_in1, HIGH);
    digitalWrite(L298N_in2, LOW);

    // Bánh trái
    digitalWrite(L298N_in3, HIGH);
    digitalWrite(L298N_in4, LOW);

    // 2. Xuất xung PWM để 2 động cơ quay cùng tốc độ
    analogWrite(L298N_enA, MOTOR_SPEED);
    analogWrite(L298N_enB, MOTOR_SPEED);

    Serial.println(">> 2 dong co dang quay tien (Forward)!");
}

void loop() {
    // 2 động cơ đã được kích hoạt chạy liên tục ở hàm setup()
    delay(1000);
}

