#!/usr/bin/env python3
"""Ordinary ROS node: TwistStamped -> bounded serial wheel commands."""

import math
import sys
import time

from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
import serial
from std_msgs.msg import String

from bumperbot_serial.protocol import CommandPolicy, STOP_PACKET, encode_wheels


class SerialMotorNode(Node):
    def __init__(self):
        super().__init__('serial_motor_node')
        self.serial_port = None
        self.failed = False
        self.was_moving = False
        defaults = {
            'serial_port': '/dev/ttyUSB0',
            'baud_rate': 115200,
            'cmd_vel_topic': '/bumperbot_controller/cmd_vel',
            'wheel_radius': 0.034,
            'wheel_separation': 0.2565,
            'max_linear_velocity': 0.10,
            'max_angular_velocity': 0.50,
            'max_wheel_velocity': 5.0,
            'command_timeout': 0.25,
            'send_rate': 20.0,
            'startup_delay': 2.0,
            'left_direction': 1,
            'right_direction': 1,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        def value(name):
            return self.get_parameter(name).value
        self.policy = CommandPolicy(**{
            name: value(name) for name in (
                'wheel_radius', 'wheel_separation', 'max_linear_velocity',
                'max_angular_velocity', 'max_wheel_velocity', 'command_timeout')
        })
        rate = value('send_rate')
        delay = value('startup_delay')
        if not math.isfinite(rate) or not 10.0 <= rate <= 100.0:
            raise ValueError('send_rate must be within 10..100 Hz')
        if not math.isfinite(delay) or not 0.0 <= delay <= 10.0:
            raise ValueError('startup_delay must be within 0..10 seconds')
        self.left_direction = value('left_direction')
        self.right_direction = value('right_direction')
        if self.left_direction not in (-1, 1) or self.right_direction not in (-1, 1):
            raise ValueError('left_direction and right_direction must be -1 or 1')
        if value('use_sim_time'):
            raise ValueError('This physical motor test requires use_sim_time:=false')

        self.rx_publisher = self.create_publisher(String, '~/serial_rx', 10)
        self.tx_publisher = self.create_publisher(String, '~/serial_tx', 10)
        self.subscription = self.create_subscription(
            TwistStamped, value('cmd_vel_topic'), self.on_command, qos_profile_sensor_data)
        self.timer = self.create_timer(
            1.0 / rate, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.timer.cancel()
        port = value('serial_port')
        self.get_logger().info(f'Opening {port} at {value("baud_rate")} baud')
        try:
            # Exclusive ownership prevents another driver opening the same port.
            # RX is nonblocking; TX has a bounded timeout and never calls flush().
            self.serial_port = serial.Serial(
                port, baudrate=value('baud_rate'), timeout=0,
                write_timeout=0.02, exclusive=True)
            self._write(STOP_PACKET)
            time.sleep(delay)  # Allow a board reset caused by opening USB serial.
            self.serial_port.reset_input_buffer()
            self._write(STOP_PACKET)
        except BaseException:
            self.close_serial()
            raise
        self.timer.reset()
        self.get_logger().info(
            f'Serial ready; listening on {value("cmd_vel_topic")} (TwistStamped). '
            f'Limits: {value("max_linear_velocity")} m/s, '
            f'{value("max_angular_velocity")} rad/s; timeout '
            f'{value("command_timeout")} s. No ros2_control required.')

    def on_command(self, message):
        stamp = message.header.stamp
        if stamp.sec == 0 and stamp.nanosec == 0:
            self.policy.stop()
            self.get_logger().warning(
                'Rejected zero timestamp; use header: auto for ros2 topic pub.',
                throttle_duration_sec=2.0)
            return
        age = (self.get_clock().now().nanoseconds -
               (stamp.sec * 1_000_000_000 + stamp.nanosec)) / 1_000_000_000
        if not self.policy.accept(
                message.twist.linear.x, message.twist.angular.z, age, time.monotonic()):
            self.get_logger().warning(
                'Rejected invalid or expired velocity command; stopping.',
                throttle_duration_sec=2.0)

    def _write(self, packet):
        if self.serial_port.write(packet) != len(packet):
            raise serial.SerialTimeoutException('Incomplete serial write')

    def tick(self):
        # Expiry uses monotonic time, independent of ROS/system clock adjustments.
        self.policy.packet(time.monotonic())
        moving = self.policy.left != 0.0 or self.policy.right != 0.0
        if self.was_moving and not moving:
            self.get_logger().info('Command expired or stopped; sending zero wheel velocities.')
        self.was_moving = moving
        packet = encode_wheels(
            self.policy.left * self.left_direction,
            self.policy.right * self.right_direction)
        try:
            self._write(packet)
            self.tx_publisher.publish(String(data=packet.decode('ascii')))
            count = min(self.serial_port.in_waiting, 4096)
            if count:
                received = self.serial_port.read(count)
                self.rx_publisher.publish(String(data=received.decode('utf-8', errors='replace')))
        except (serial.SerialException, OSError) as error:
            self.failed = True
            self.timer.cancel()
            self.policy.stop()
            self.get_logger().error(f'Serial I/O failed: {error}. Stopping and closing port.')
            self.close_serial()
            # Unwind the executor before destroying ROS entities. Shutting down
            # the context inside this callback can stall cleanup on Humble.
            raise RuntimeError(f'Serial link failed: {error}') from error

    def close_serial(self):
        if self.serial_port is None:
            return
        try:
            if self.serial_port.is_open:
                self._write(STOP_PACKET)
        except (serial.SerialException, OSError) as error:
            # A disconnected link cannot carry a stop; firmware needs its own watchdog.
            print(f'Could not send final stop packet: {error}', file=sys.stderr)
        finally:
            try:
                self.serial_port.close()
            except (serial.SerialException, OSError) as error:
                print(f'Could not close serial port: {error}', file=sys.stderr)
            finally:
                self.serial_port = None


def main(args=None):
    rclpy.init(args=args)
    node = None
    result = 0
    try:
        node = SerialMotorNode()
        rclpy.spin(node)
        result = int(node.failed)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as error:
        print(f'Serial motor node failed: {error}', file=sys.stderr)
        result = 1
    finally:
        if node is not None:
            node.close_serial()
            node.destroy_node()
        rclpy.try_shutdown()
    return result


if __name__ == '__main__':
    sys.exit(main())
