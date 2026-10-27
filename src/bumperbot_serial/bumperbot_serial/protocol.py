"""Differential-drive commands for the existing r/l, p/n serial firmware."""

import math


STOP_PACKET = b'rp00.00,lp00.00,'


def encode_wheels(left, right):
    """Encode radians/second, right wheel first, with five numeric characters."""
    if not all(math.isfinite(value) and abs(value) <= 99.99 for value in (left, right)):
        raise ValueError('Wheel velocity must be finite and within +/-99.99 rad/s')

    def field(prefix, value):
        # Select the sign after rounding so tiny negative values stop cleanly.
        value = round(value, 2)
        return f'{prefix}{"n" if value < 0 else "p"}{abs(value):05.2f},'

    return (field('r', right) + field('l', left)).encode('ascii')


class CommandPolicy:
    """Validate stamped commands and expire them using a monotonic clock."""

    def __init__(self, wheel_radius=0.034, wheel_separation=0.2565,
                 max_linear_velocity=0.10, max_angular_velocity=0.50,
                 max_wheel_velocity=5.0, command_timeout=0.25):
        values = (wheel_radius, wheel_separation, max_linear_velocity,
                  max_angular_velocity, max_wheel_velocity, command_timeout)
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise ValueError('Geometry, limits and command_timeout must be finite and positive')
        if max_wheel_velocity > 99.99:
            raise ValueError('max_wheel_velocity must not exceed the firmware limit of 99.99')
        self.wheel_radius = wheel_radius
        self.wheel_separation = wheel_separation
        self.max_linear_velocity = max_linear_velocity
        self.max_angular_velocity = max_angular_velocity
        self.max_wheel_velocity = max_wheel_velocity
        self.command_timeout = command_timeout
        self.stop()

    def stop(self):
        self.left = self.right = 0.0
        self.expires_at = float('-inf')

    def accept(self, linear, angular, age, now):
        """Reject malformed, stale or future-dated commands and clear motion."""
        if (not all(math.isfinite(value) for value in (linear, angular, age, now))
                or age >= self.command_timeout or age < -0.10):
            self.stop()
            return False
        linear = max(-self.max_linear_velocity, min(self.max_linear_velocity, linear))
        angular = max(-self.max_angular_velocity, min(self.max_angular_velocity, angular))
        self.left = (linear - angular * self.wheel_separation / 2.0) / self.wheel_radius
        self.right = (linear + angular * self.wheel_separation / 2.0) / self.wheel_radius
        # Scale both wheels together to preserve curvature when limiting speed.
        scale = max(1.0, abs(self.left) / self.max_wheel_velocity,
                    abs(self.right) / self.max_wheel_velocity)
        self.left /= scale
        self.right /= scale
        self.expires_at = now + self.command_timeout - max(0.0, age)
        return True

    def packet(self, now):
        if now >= self.expires_at:
            self.stop()
        return encode_wheels(self.left, self.right)
