#!/usr/bin/env python3

import serial
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SimpleSerialReceiver(Node):
    def __init__(self):
        super().__init__('simple_serial_receiver')

        self.publisher_ = self.create_publisher(String, 'serial_receiver', 10)
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('timer_period', 0.01)

        self.port_ = self.get_parameter('port').value
        self.baudrate_ = self.get_parameter('baudrate').value
        self.timer_period_ = self.get_parameter('timer_period').value
        self.arduino_ = None

        try:
            self.arduino_ = serial.Serial(
                port=self.port_, baudrate=self.baudrate_, timeout=0.1
            )
        except serial.SerialException as error:
            self.get_logger().error(
                f'Cannot open serial port {self.port_}: {error}'
            )
            raise

        self.timer_ = self.create_timer(self.timer_period_, self.timer_callback)
        self.get_logger().info(
            f'Reading {self.port_} at {self.baudrate_} baud '
            f'({1.0 / self.timer_period_:.0f} Hz)'
        )

    def timer_callback(self):
        if not self.arduino_ or not self.arduino_.is_open:
            return

        try:
            data = self.arduino_.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            self.get_logger().warning('Received non-UTF-8 serial data')
            return
        except serial.SerialException as error:
            self.get_logger().error(f'Serial read failed: {error}')
            return

        if not data:
            return

        message = String()
        message.data = data
        self.publisher_.publish(message)

    def destroy_node(self):
        if self.arduino_ and self.arduino_.is_open:
            self.arduino_.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SimpleSerialReceiver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
