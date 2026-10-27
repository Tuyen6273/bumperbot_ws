#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus

PWR_MGMT_1     = 0x6B
SMPLRT_DIV     = 0x19
CONFIG         = 0x1A
GYRO_CONFIG    = 0x1B
ACCEL_CONFIG   = 0x1C
INT_ENABLE     = 0x38
ACCEL_XOUT_H   = 0x3B
ACCEL_YOUT_H   = 0x3D
ACCEL_ZOUT_H   = 0x3F
GYRO_XOUT_H    = 0x43
GYRO_YOUT_H    = 0x45
GYRO_ZOUT_H    = 0x47
DEVICE_ADDRESS = 0x68

class MPU6050(Node):
    def __init__(self):
        super().__init__("Mpu6050")
        self.pub_ = self.create_publisher(Imu, "/imu/out", 10)

        self.imu_msg_ = Imu()
        self.imu_msg_.header.frame_id = "base_footprint"
        self.is_connected_ = False
        self.bus_ = None
        self.init_i2c()


        self.frequency_= 0.01
        self.timer_ = self.create_timer(self.frequency_, self.timerCallback)
        self.get_logger().info("MPU6050 node started; publishing on /imu/out.")

    def timerCallback(self):
        if not self.is_connected_:
            self.get_logger().warn(
                "MPU6050 disconnected; retrying I2C initialization.",
                throttle_duration_sec=2.0,
            )
            self.init_i2c()
            return

        try:
            acel_x = self.read_raw_data(ACCEL_XOUT_H)
            acel_y = self.read_raw_data(ACCEL_YOUT_H)
            acel_z = self.read_raw_data(ACCEL_ZOUT_H)

            gyro_x = self.read_raw_data(GYRO_XOUT_H)
            gyro_y = self.read_raw_data(GYRO_YOUT_H)
            gyro_z = self.read_raw_data(GYRO_ZOUT_H)

            # ACCEL_CONFIG=0: 16384 LSB/g; GYRO_CONFIG=24: 16.4 LSB/(deg/s).
            self.imu_msg_.linear_acceleration.x = acel_x / 16384.0 * 9.80665
            self.imu_msg_.linear_acceleration.y = acel_y / 16384.0 * 9.80665
            self.imu_msg_.linear_acceleration.z = acel_z / 16384.0 * 9.80665
            self.imu_msg_.angular_velocity.x = math.radians(gyro_x / 16.4)
            self.imu_msg_.angular_velocity.y = math.radians(gyro_y / 16.4)
            self.imu_msg_.angular_velocity.z = math.radians(gyro_z / 16.4)

            self.imu_msg_.header.stamp = self.get_clock().now().to_msg()
            self.pub_.publish(self.imu_msg_)
            self.get_logger().info(
                f"[IMU] Accel (m/s²): X={self.imu_msg_.linear_acceleration.x:.2f}, "
                f"Y={self.imu_msg_.linear_acceleration.y:.2f}, "
                f"Z={self.imu_msg_.linear_acceleration.z:.2f} | "
                f"Gyro (rad/s): X={self.imu_msg_.angular_velocity.x:.2f}, "
                f"Y={self.imu_msg_.angular_velocity.y:.2f}, "
                f"Z={self.imu_msg_.angular_velocity.z:.2f}",
                throttle_duration_sec=1.0,
            )
        except OSError as e:
            self.get_logger().error(f"Failed to read MPU6050 over I2C: {e}")
            self.is_connected_ = False


    def init_i2c(self):
        try:
            if self.bus_ is not None:
                self.bus_.close()
                self.bus_ = None
            self.bus_ = smbus.SMBus(1)
            self.bus_.write_byte_data(DEVICE_ADDRESS, SMPLRT_DIV, 7)
            self.bus_.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 1)
            self.bus_.write_byte_data(DEVICE_ADDRESS, CONFIG, 0)
            self.bus_.write_byte_data(DEVICE_ADDRESS, GYRO_CONFIG, 24)
            self.bus_.write_byte_data(DEVICE_ADDRESS, ACCEL_CONFIG, 0)
            self.bus_.write_byte_data(DEVICE_ADDRESS, INT_ENABLE, 1)
            self.is_connected_ = True
            self.get_logger().info("MPU6050 I2C connection configured successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize I2C: {e}", throttle_duration_sec=2.0)
            self.is_connected_ = False
    def read_raw_data(self, addr):
        high = self.bus_.read_byte_data(DEVICE_ADDRESS, addr)
        low = self.bus_.read_byte_data(DEVICE_ADDRESS, addr + 1)
        value = ((high << 8) | low)
        if (value >= 32768):
            value = value - 65536
        return value

def main():
    rclpy.init()

    mpu6050 = MPU6050()
    try:
        rclpy.spin(mpu6050)
    except KeyboardInterrupt:
        pass
    finally:
        if mpu6050.bus_ is not None:
            mpu6050.bus_.close()
        mpu6050.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
