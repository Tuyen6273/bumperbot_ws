/*
  ESP32: ĐO SỐ XUNG ENCODER TRONG 1 VÒNG QUAY

  Kết nối:
  - Encoder pha A -> GPIO 18
  - Encoder pha B -> GPIO 19
  - Encoder VCC   -> 3.3V
  - Encoder GND   -> GND

  Điều khiển qua Serial Monitor, baud rate 115200:
  - Gửi r: reset bộ đếm và bắt đầu đo
  - Quay trục đầu ra đúng 1 vòng
  - Gửi s: dừng đo và in số xung
*/


// Pha A tạo interrupt để đếm xung.
#define ENCODER_A 18

// Pha B chỉ dùng để xác định chiều quay.
#define ENCODER_B 19


// Biến đếm xung encoder.
volatile long encoder_ticks = 0;

// Cho biết hiện có đang thực hiện phép đo không.
volatile bool is_measuring = false;

// Mutex để ESP32 đọc/ghi biến từ interrupt an toàn.
portMUX_TYPE encoder_mutex = portMUX_INITIALIZER_UNLOCKED;


// Hàm chạy khi pha A chuyển từ LOW sang HIGH.
void IRAM_ATTR encoderCallback() {
  portENTER_CRITICAL_ISR(&encoder_mutex);

  // Chỉ đếm xung khi người dùng đã gửi lệnh "r".
  if (is_measuring) {
    /*
      Đếm có dấu:
      - Pha B HIGH: tăng xung
      - Pha B LOW: giảm xung

      Dùng abs() khi in kết quả để có tổng số xung,
      không phụ thuộc chiều quay.
    */
    if (digitalRead(ENCODER_B) == HIGH) {
      encoder_ticks++;
    } else {
      encoder_ticks--;
    }
  }

  portEXIT_CRITICAL_ISR(&encoder_mutex);
}


void setup() {
  Serial.begin(115200);

  // Thiết lập hai chân encoder là đầu vào.
  pinMode(ENCODER_A, INPUT);
  pinMode(ENCODER_B, INPUT);

  /*
    Gắn interrupt vào pha A.
    Mỗi cạnh lên của pha A được tính là một xung.
  */
  attachInterrupt(
    digitalPinToInterrupt(ENCODER_A),
    encoderCallback,
    RISING
  );

  Serial.println("\n--- DO SO XUNG ENCODER ---");
  Serial.println("Gui 'r' de reset va bat dau do.");
  Serial.println("Quay truc dau ra DUNG 1 vong.");
  Serial.println("Gui 's' de dung va xem ket qua.");
}


void loop() {
  // Kiểm tra lệnh gửi từ Serial Monitor.
  if (Serial.available() > 0) {
    char command = Serial.read();

    // r = reset và bắt đầu đếm xung.
    if (command == 'r' || command == 'R') {
      portENTER_CRITICAL(&encoder_mutex);

      encoder_ticks = 0;
      is_measuring = true;

      portEXIT_CRITICAL(&encoder_mutex);

      Serial.println("Da reset. Hay quay truc dau ra dung 1 vong.");
    }

    // s = dừng và hiển thị kết quả.
    if (command == 's' || command == 'S') {
      long ticks;

      portENTER_CRITICAL(&encoder_mutex);

      is_measuring = false;
      ticks = encoder_ticks;

      portEXIT_CRITICAL(&encoder_mutex);

      Serial.println("\n--- KET QUA ---");
      Serial.print("Tong so xung (pha A, RISING): ");
      Serial.println(abs(ticks));

      Serial.print("Chieu quay: ");
      if (ticks >= 0) {
        Serial.println("duong");
      } else {
        Serial.println("am");
      }

      Serial.println("Gui 'r' de do lai.");
    }
  }
}