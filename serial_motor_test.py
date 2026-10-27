import serial
import time

with serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1) as ser:
    time.sleep(2)
    try:
        ser.write(b"rn3.00,ln3.00,")
        while True:
            data = ser.readline().decode(errors="replace").strip()
            if data:
                print("RX:", data)
    except KeyboardInterrupt:
        ser.write(b"rn0.00,ln0.00,")
        ser.flush()
