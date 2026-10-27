from launch import LaunchDescription
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os
from launch_ros.actions import Node

def generate_launch_description():
    bumperbot_description_dir = get_package_share_directory("bumperbot_description")
    model = os.path.join(bumperbot_description_dir,
                                    "urdf", "bumperbot.urdf.xacro")
    robot_description = ParameterValue(Command([
            "xacro ", 
            model,
            " is_sim:=False"
    ]),
    value_type=str)

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}] 
        # tham số robot_description được truyền 
        # vào node robot_state_publisher, để node 
        # này được sinh ra từ file urdf của robot, 
        # và có thể xuất ra các thông tin về trạng thái của robot trong ros2
    )

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{"robot_description": robot_description, "use_sim_time": False},
                    os.path.join(get_package_share_directory("bumperbot_controller"),
                                  "config", "bumperbot_controllers.yaml")],
    )

    imu_driver_node = Node(
        package="bumperbot_firmware",
        executable="Mpu6050.py",
    )

    

    return LaunchDescription([
        robot_state_publisher_node,
        controller_manager,
        imu_driver_node
    ])