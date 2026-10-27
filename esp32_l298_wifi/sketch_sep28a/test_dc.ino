// Điều khiển động cơ DC bằng Arduino + L298N + ROS 2 qua Serial

// Chân L298N kết nối với Arduino
#define ENA 9     // Enable A (PWM)
#define IN1 12    // Input 1
#define IN2 13    // Input 2

double command = 0.0;

void setup() {
  // Khai báo các chân điều khiển là đầu ra
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Thiết lập chiều quay: chiều kim đồng hồ
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Giao tiếp Serial với ROS 2
  Serial.begin(115200);
}

void loop() {
  // Kiểm tra xem ROS 2 có gửi lệnh mới qua Serial không
  if (Serial.available() > 0) {
    // Đọc chuỗi lệnh, ví dụ: "1.0"
    command = Serial.readString().toDouble();
  }

  // Chuyển lệnh thành giá trị PWM.
  // PWM Arduino nằm trong khoảng 0–255.
  int motorSpeed = (int)(command * 100);

  // Đảm bảo giá trị PWM không vượt phạm vi hợp lệ
  motorSpeed = constrain(motorSpeed, 0, 255);

  // Xuất PWM để điều chỉnh tốc độ động cơ
  analogWrite(ENA, motorSpeed);
}