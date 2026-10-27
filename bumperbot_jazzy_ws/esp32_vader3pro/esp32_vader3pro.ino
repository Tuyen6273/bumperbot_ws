// ESP32 + Flydigi Vader 3 Pro (Bluetooth) receiver
// Library: Bluepad32
// Open Serial Monitor at 115200 baud after uploading.

#include <Bluepad32.h>

ControllerPtr controller = nullptr;

void onControllerConnected(ControllerPtr ctl) {
  if (controller != nullptr) {
    Serial.println("Another controller was ignored (one controller only).");
    return;
  }

  controller = ctl;
  ControllerProperties properties = ctl->getProperties();
  Serial.printf("Connected: %s (VID=0x%04x PID=0x%04x)\n",
                ctl->getModelName().c_str(),
                properties.vendor_id, properties.product_id);
  ctl->setPlayerLEDs(0x01);  // Optional: show player 1 LED.
}

void onControllerDisconnected(ControllerPtr ctl) {
  if (controller == ctl) {
    controller = nullptr;
    Serial.println("Controller disconnected");
  }
}

void printGamepadState(ControllerPtr ctl) {
  // Bluepad32 normalizes the axes. Center is approximately 0.
  // Y is normally negative when the left stick is pushed forward.
  Serial.printf(
      "LX=%d LY=%d RX=%d RY=%d | LT=%d RT=%d | dpad=0x%02x buttons=0x%04x misc=0x%02x\n",
      ctl->axisX(), ctl->axisY(), ctl->axisRX(), ctl->axisRY(),
      ctl->brake(), ctl->throttle(), ctl->dpad(), ctl->buttons(), ctl->miscButtons());
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Starting Bluepad32. Put Vader 3 Pro in Bluetooth pairing mode now.");

  BP32.setup(&onControllerConnected, &onControllerDisconnected);

  // Uncomment for a first pairing attempt, or to remove an old pairing.
  // BP32.forgetBluetoothKeys();

  // Keep this enabled while pairing a new controller. Set false after it has
  // paired if you want ESP32 to accept only remembered controllers.
  BP32.enableNewBluetoothConnections(true);
}

void loop() {
  BP32.update();  // Required: handles Bluetooth and invokes callbacks.

  if (controller != nullptr && controller->isConnected() && controller->hasData()) {
    if (controller->isGamepad()) {
      printGamepadState(controller);
    }
  }

  delay(20);  // Print at <= 50 Hz so Serial Monitor remains readable.
}
