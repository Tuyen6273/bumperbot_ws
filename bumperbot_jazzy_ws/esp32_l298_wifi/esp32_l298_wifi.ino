/*
 * UDP receiver for a two-wheel robot with an L298 driver.
 *
 * Incoming UDP packet:  <sequence> <left_pwm> <right_pwm>\n
 * left_pwm/right_pwm range: -255..255.  Sign selects direction.
 * The ESP32 performs no kinematics: it only applies the requested PWM.
 */

#include <WiFi.h>
#include <WiFiUdp.h>

// Change these before uploading.
constexpr char WIFI_SSID[] = "YOUR_WIFI_NAME";
constexpr char WIFI_PASSWORD[] = "YOUR_WIFI_PASSWORD";
constexpr uint16_t UDP_PORT = 4210;

// L298 pins supplied by the user.
constexpr int ENB = 32;  // motor B speed PWM
constexpr int IND = 33;  // motor B direction 2
constexpr int INC = 25;  // motor B direction 1
constexpr int INA = 26;  // motor A direction 1
constexpr int INB = 27;  // motor A direction 2
constexpr int ENA = 14;  // motor A speed PWM

constexpr int PWM_FREQUENCY_HZ = 20000;
constexpr int PWM_RESOLUTION_BITS = 8;
constexpr int PWM_CHANNEL_A = 0;
constexpr int PWM_CHANNEL_B = 1;
constexpr uint32_t COMMAND_TIMEOUT_MS = 300;

WiFiUDP udp;
uint32_t last_command_ms = 0;

void setMotor(int pwm, int pin_forward, int pin_reverse, int pwm_channel) {
  pwm = constrain(pwm, -255, 255);

  if (pwm > 0) {
    digitalWrite(pin_forward, HIGH);
    digitalWrite(pin_reverse, LOW);
  } else if (pwm < 0) {
    digitalWrite(pin_forward, LOW);
    digitalWrite(pin_reverse, HIGH);
  } else {
    // Coast when stopped. Change both to HIGH if your hardware requires brake.
    digitalWrite(pin_forward, LOW);
    digitalWrite(pin_reverse, LOW);
  }
  ledcWrite(pwm_channel, abs(pwm));
}

void stopMotors() {
  setMotor(0, INA, INB, PWM_CHANNEL_A);
  setMotor(0, INC, IND, PWM_CHANNEL_B);
}

void setup() {
  Serial.begin(115200);

  pinMode(INA, OUTPUT);
  pinMode(INB, OUTPUT);
  pinMode(INC, OUTPUT);
  pinMode(IND, OUTPUT);
  ledcSetup(PWM_CHANNEL_A, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcSetup(PWM_CHANNEL_B, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(ENA, PWM_CHANNEL_A);
  ledcAttachPin(ENB, PWM_CHANNEL_B);
  stopMotors();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print('.');
  }
  Serial.printf("\nESP32 address: %s\n", WiFi.localIP().toString().c_str());

  udp.begin(UDP_PORT);
  last_command_ms = millis();
  Serial.printf("Listening for UDP packets on port %u\n", UDP_PORT);
}

void loop() {
  const int packet_size = udp.parsePacket();
  if (packet_size > 0) {
    char buffer[64];
    const int count = udp.read(buffer, sizeof(buffer) - 1);
    if (count > 0) {
      buffer[count] = '\0';
      unsigned long sequence;
      int left_pwm;
      int right_pwm;
      if (sscanf(buffer, "%lu %d %d", &sequence, &left_pwm, &right_pwm) == 3) {
        setMotor(left_pwm, INA, INB, PWM_CHANNEL_A);
        setMotor(right_pwm, INC, IND, PWM_CHANNEL_B);
        last_command_ms = millis();

        // Acknowledge to the computer so it can tell that Wi-Fi is working.
        char reply[64];
        const int reply_len = snprintf(reply, sizeof(reply), "ACK %lu %d %d\n",
                                       sequence, constrain(left_pwm, -255, 255),
                                       constrain(right_pwm, -255, 255));
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.write(reinterpret_cast<const uint8_t*>(reply), reply_len);
        udp.endPacket();
      }
    }
  }

  // Safety: if the computer, Wi-Fi, or Python program stops, stop the robot.
  if (millis() - last_command_ms > COMMAND_TIMEOUT_MS) {
    stopMotors();
  }
}
