import math

import pytest

from bumperbot_serial.protocol import CommandPolicy, STOP_PACKET, encode_wheels


def test_signed_fixed_width_firmware_packets():
    assert encode_wheels(-2.5, 1.0) == b'rp01.00,ln02.50,'
    assert encode_wheels(0.0, -0.001) == STOP_PACKET
    for value in (float('nan'), float('inf'), 100.0):
        with pytest.raises(ValueError):
            encode_wheels(value, 0.0)


def test_turning_and_saturation_preserve_wheel_ratio():
    policy = CommandPolicy(max_wheel_velocity=2.0)
    assert policy.accept(0.1, 0.5, age=0.0, now=10.0)
    expected_ratio = (0.1 - 0.5 * 0.2565 / 2) / (0.1 + 0.5 * 0.2565 / 2)
    assert policy.right == pytest.approx(2.0)
    assert policy.left / policy.right == pytest.approx(expected_ratio)
    policy.accept(0.0, -0.5, age=0.0, now=11.0)
    assert policy.left > 0 and policy.right < 0
    assert policy.left == pytest.approx(-policy.right)


def test_old_command_expires_based_on_stamp_and_monotonic_deadline():
    policy = CommandPolicy(command_timeout=0.25)
    assert policy.packet(10.0) == STOP_PACKET
    assert policy.accept(0.05, 0.0, age=0.20, now=10.0)
    assert policy.packet(10.04) != STOP_PACKET
    assert policy.packet(10.051) == STOP_PACKET
    assert policy.packet(100.0) == STOP_PACKET


@pytest.mark.parametrize('linear,angular,age', [
    (0.05, 0.0, 0.25), (0.05, 0.0, -0.2),
    (math.nan, 0.0, 0.0), (0.0, math.inf, 0.0), (0.0, 0.0, math.nan),
])
def test_invalid_command_clears_previous_motion(linear, angular, age):
    policy = CommandPolicy()
    policy.accept(0.05, 0.0, age=0.0, now=10.0)
    assert not policy.accept(linear, angular, age=age, now=10.01)
    assert policy.packet(10.02) == STOP_PACKET


def test_body_velocity_limits_and_invalid_configuration():
    policy = CommandPolicy()
    policy.accept(1.0, 0.0, age=0.0, now=10.0)
    assert policy.left * policy.wheel_radius == pytest.approx(0.1)
    for parameters in ({'wheel_radius': 0.0}, {'command_timeout': -1.0},
                       {'max_wheel_velocity': 100.0}, {'wheel_separation': math.nan}):
        with pytest.raises(ValueError):
            CommandPolicy(**parameters)
