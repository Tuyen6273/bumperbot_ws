import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    controller_config = os.path.join(
        get_package_share_directory("bumperbot_controller"),
        "config", "bumperbot_controllers.yaml")

    wheel_separation_arg = DeclareLaunchArgument(
        "wheel_separation",
        default_value="0.2565"
    )

    wheel_radius_arg = DeclareLaunchArgument(
        "wheel_radius",
        default_value="0.034"
    )

    deadzone_arg = DeclareLaunchArgument(
        "deadzone_joystick",
        default_value="0.2"
    )
    max_linear_speed_arg = DeclareLaunchArgument(
        "max_linear_speed",
        default_value="0.8"
    )

    max_angular_speed_arg = DeclareLaunchArgument(
        "max_angular_speed",
        default_value="0.8"
    )

    wheel_radius = LaunchConfiguration("wheel_radius")
    wheel_separation = LaunchConfiguration("wheel_separation")
    deadzone_joystick = LaunchConfiguration("deadzone_joystick")
    max_linear_speed = LaunchConfiguration("max_linear_speed")
    max_angular_speed = LaunchConfiguration("max_angular_speed")

    joint_state_broadcaster_spawner =Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--param-file", controller_config
        ]
    )

    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "bumperbot_controller",
            "--controller-manager",
            "/controller_manager",
            "--param-file", controller_config
        ],
    )

    joystick_publisher = Node(
        package="bumberbot_py_examples",
        executable="joystick_publisher",
        parameters=[
            {"wheel_radius": wheel_radius, 
            "wheel_separation": wheel_separation,
            "deadzone_joystick": deadzone_joystick, 
            "max_linear_speed": max_linear_speed,
            "max_angular_speed": max_angular_speed}
        ],
     )
    
    return LaunchDescription([
        wheel_radius_arg,
        wheel_separation_arg,
        deadzone_arg,
        max_linear_speed_arg,
        max_angular_speed_arg,
        joint_state_broadcaster_spawner,
        diff_drive_controller,
        joystick_publisher
    ])

# ROS 2 Control: khởi động controller trong Gazebo
# - Plugin gz_ros2_control trong URDF/Xacro tạo và chạy node /controller_manager.
# - File YAML định nghĩa các controller:
#   - joint_state_broadcaster: xuất trạng thái các joint.
#   - simple_velocity_controller: nhận lệnh vận tốc cho hai bánh xe.
# - File controller.launch.py dùng executable controller_manager/spawner để nạp và kích hoạt từng controller.
# Node(
#     package='controller_manager',
#     executable='spawner',
#     arguments=[
#         'joint_state_broadcaster',
#         '--controller-manager',
#         '/controller_manager',
#     ],
# )
# - Cần spawn hai controller:
#   1. joint_state_broadcaster
#   2. simple_velocity_controller
# - controller.launch.py phải chạy sau khi Gazebo đã spawn robot, vì khi đó plugin mới tạo /controller_manager.
# - Nên include launch controller vào launch Gazebo và trì hoãn khoảng vài giây bằng TimerAction để tránh lỗi không kết nối được controller manager.
# - Cần khai báo thư mục launch trong CMakeLists.txt:
# install(DIRECTORY config launch
#   DESTINATION share/${PROJECT_NAME}/
# )
# - Dependencies cần có trong package.xml:
# <exec_depend>ros2launch</exec_depend>
# <exec_depend>controller_manager</exec_depend>
# Lệnh kiểm tra controller sau khi khởi động:
# ros2 control list_controllers
# Kết quả mong đợi: joint_state_broadcaster và simple_velocity_controller ở trạng thái active.
