#!/usr/bin/env python3
"""Drive an ESP32/L298 two-wheel robot from a PC gamepad over Wi-Fi.

Install on the PC once:
    python3 -m pip install pygame

Example:
    python3 wifi_gamepad_controller.py --esp-ip 192.168.1.50

Hold the right bumper to enable the motors. Releasing it, closing the program,
or losing Wi-Fi sends a zero-PWM command. All joystick processing and
differential-drive kinematics happen here; ESP32 receives only signed PWM.
"""

import argparse
import math
import select
import socket
import sys
import time

import pygame


# Geometry supplied by the user, converted from mm to metres.
# Confirm these units: a 6.8 mm wheel is unusually small; use 0.068 if it is 6.8 cm.
WHEEL_DIAMETER_M = 0.068
WHEEL_BASE_M = 0.258
WHEEL_RADIUS_M = WHEEL_DIAMETER_M / 2.0

# Tune these safely on blocks first. MAX_WHEEL_SPEED_MPS is the linear wheel
# speed reached at PWM=255, measured on your actual robot.
MAX_LINEAR_SPEED_MPS = 0.01
MAX_ANGULAR_SPEED_RAD_S = 0.5
MAX_WHEEL_SPEED_MPS = 0.01
MAX_PWM = 180
DEADZONE = 0.12
SEND_RATE_HZ = 50.0

# Typical Xbox-compatible layout. Print the raw values below and adjust if your
# controller uses other indices.
AXIS_FORWARD = 1       # left stick vertical; up is normally negative
AXIS_TURN = 3          # right stick horizontal
BUTTON_ENABLE = 5      # right bumper: must be held as a safety/dead-man switch


def apply_deadzone(value: float) -> float:
    """Return a continuous, rescaled axis value after the central deadzone."""
    if abs(value) <= DEADZONE:
        return 0.0
    return math.copysign((abs(value) - DEADZONE) / (1.0 - DEADZONE), value)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def twist_to_pwm(linear_mps: float, angular_rad_s: float) -> tuple[int, int, float, float]:
    """Differential-drive inverse kinematics, then convert wheel speeds to PWM."""
    left_mps = linear_mps - angular_rad_s * WHEEL_BASE_M / 2.0
    right_mps = linear_mps + angular_rad_s * WHEEL_BASE_M / 2.0

    # Wheel angular rates are calculated here for diagnostics/control extension.
    left_rad_s = left_mps / WHEEL_RADIUS_M
    right_rad_s = right_mps / WHEEL_RADIUS_M

    left_pwm = round(MAX_PWM * clamp(left_mps / MAX_WHEEL_SPEED_MPS, -1.0, 1.0))
    right_pwm = round(MAX_PWM * clamp(right_mps / MAX_WHEEL_SPEED_MPS, -1.0, 1.0))
    return left_pwm, right_pwm, left_rad_s, right_rad_s


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("esp_ip", nargs="?", default="192.168.128.111", help="IP printed by ESP32 Serial Monitor")
    parser.add_argument("port", nargs="?", type=int, default=4210, help="ESP32 UDP port")
    args = parser.parse_args()

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("Không tìm thấy tay cầm. Kết nối tay cầm với MÁY TÍNH trước.", file=sys.stderr)
        return 1
    gamepad = pygame.joystick.Joystick(0)
    gamepad.init()
    print(f"Gamepad: {gamepad.get_name()}")
    print("Giữ RB để chạy. Ctrl+C để dừng.")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    target = (args.esp_ip, args.port)
    sequence = 0
    next_send = time.monotonic()
    last_ack = 0.0

    try:
        while True:
            pygame.event.pump()
            if time.monotonic() < next_send:
                time.sleep(0.001)
                continue
            next_send += 1.0 / SEND_RATE_HZ

            forward = -apply_deadzone(gamepad.get_axis(AXIS_FORWARD))
            turn = apply_deadzone(gamepad.get_axis(AXIS_TURN))
            enabled = bool(gamepad.get_button(BUTTON_ENABLE))
            linear = forward * MAX_LINEAR_SPEED_MPS if enabled else 0.0
            angular = turn * MAX_ANGULAR_SPEED_RAD_S if enabled else 0.0
            left_pwm, right_pwm, left_rad_s, right_rad_s = twist_to_pwm(linear, angular)

            sequence += 1
            sock.sendto(f"{sequence} {left_pwm} {right_pwm}\n".encode(), target)

            while select.select([sock], [], [], 0)[0]:
                reply, _ = sock.recvfrom(64)
                last_ack = time.monotonic()
                print(f"\r{reply.decode().strip():<25} pwm=({left_pwm:4d},{right_pwm:4d}) "
                      f"wheel rad/s=({left_rad_s:5.1f},{right_rad_s:5.1f})", end="", flush=True)

            if time.monotonic() - last_ack > 1.0:
                print("\rChưa nhận ACK từ ESP32. Kiểm tra IP/Wi-Fi.                         ", end="", flush=True)
    except KeyboardInterrupt:
        print("\nĐang dừng robot...")
    finally:
        # Send several stop commands in case one UDP packet is lost.
        for _ in range(3):
            sequence += 1
            sock.sendto(f"{sequence} 0 0\n".encode(), target)
            time.sleep(0.03)
        sock.close()
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
