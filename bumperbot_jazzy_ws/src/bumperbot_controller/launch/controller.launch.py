import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def noisy_controller(context, *args, **kwargs):
    wheel_radius = float(LaunchConfiguration("wheel_radius").perform(context))
    wheel_separation = float(LaunchConfiguration("wheel_separation").perform(context))
    wheel_radius_error = float(LaunchConfiguration("wheel_radius_error").perform(context))
    wheel_separation_error = float(LaunchConfiguration("wheel_separation_error").perform(context))

    noisy_controller_py = Node(
        package="bumperbot_controller",
        executable="noisy_controller.py",
        parameters=[
            {"wheel_radius": wheel_radius + wheel_radius_error,
             "wheel_separation": wheel_separation + wheel_separation_error},
        ],
    )
    return [noisy_controller_py]

def generate_launch_description():
    controller_config = os.path.join(
        get_package_share_directory("bumperbot_controller"),
        "config", "bumperbot_controllers.yaml")

    use_python_arg = DeclareLaunchArgument(
        "use_python",
        default_value= "True"
    ) # tạo ra một điều kiện để chọn file chạy thôi 

    wheel_separation_arg = DeclareLaunchArgument(
        "wheel_separation",
        default_value="0.2565"
    )

    wheel_radius_arg = DeclareLaunchArgument(
            "wheel_radius",
            default_value="0.034"
        )

    simple_controller_arg = DeclareLaunchArgument(
        name="use_simple_controller",
        default_value= "False"
    )

    wheel_radius_error_arg = DeclareLaunchArgument(
        "wheel_radius_error",
        default_value="0.005"
    )

    wheel_seperation_error_arg = DeclareLaunchArgument(
        "wheel_separation_error",
        default_value="0.02"
    )

    use_python = LaunchConfiguration("use_python")
    wheel_radius = LaunchConfiguration("wheel_radius")
    wheel_separation = LaunchConfiguration("wheel_separation")
    use_simple_controller = LaunchConfiguration("use_simple_controller")

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
        condition = UnlessCondition(use_simple_controller) 
    )
    simple_controller = GroupAction(
        condition = IfCondition(use_simple_controller),
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "simple_velocity_controller",
                    "--controller-manager",
                    "/controller_manager",
                    "--param-file", controller_config
                ],
            ),
            
            Node(
                package="bumperbot_controller",
                executable="simple_controller.py",
                parameters=[
                    {"wheel_radius": wheel_radius, 
                    "wheel_separation": wheel_separation}
                ],
                condition = IfCondition(use_python)
            )
        ]
    )

    noisy_controller_launch = OpaqueFunction(function = noisy_controller)
    
    return LaunchDescription([
        use_python_arg,
        wheel_radius_arg,
        wheel_separation_arg,
        simple_controller_arg,
        wheel_radius_error_arg,
        wheel_seperation_error_arg,
        joint_state_broadcaster_spawner,
        diff_drive_controller,
        simple_controller,
        noisy_controller_launch,
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
