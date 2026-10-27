#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
imu_pub = None

def imuCallback(imu):
    global imu_pub # khai báo laại global trong đây để có thể có thể update giá trị biến global bên trong hàm
    imu.header.frame_id = "base_footprint_ekf"
    imu_pub.publish(imu)


def main():
    global imu_pub
    rclpy.init()
    node = Node("imu_republisher")
    imu_pub = node.create_publisher(Imu, "imu_ekf", 10)
    imu_sub = node.create_subscription(Imu, "imu/out", imuCallback, 10)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

# mỗi khi dữ liệu từ imu được đọc thì nó sẽ tạo ra một frame_id có thê là base_footprint_ekf