from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_dir = get_package_share_directory("bumperbot_localization")

    path_dir = os.path.join(package_dir, 'config', 'ekf.yaml')

    static_transform_publisher_node = Node(
        package = "tf2_ros",
        executable = "static_transform_publisher",
        arguments = ["--x", "0", "--y", "0", "--z", "0",
                     "--qx", "0", "--qy", "0", "--qz", "0", "--qw", "1",
                     "--frame-id", "base_footprint_ekf", "--child-frame-id", "imu_link_ekf"]
    )

    robot_localization = Node(
    package="robot_localization",
    executable="ekf_node",
    name="ekf_filter_node",
    output="screen",
    parameters=[path_dir],
    )

    imu_republisher_py = Node(
    package="bumperbot_localization",
    executable="imu_republisher.py",
    )

    return LaunchDescription([
        static_transform_publisher_node, 
        robot_localization,
        imu_republisher_py
    ])