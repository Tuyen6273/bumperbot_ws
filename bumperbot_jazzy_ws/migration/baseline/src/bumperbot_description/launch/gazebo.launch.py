from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription
import os 
from os import pathsep
from launch.launch_description_sources import PythonLaunchDescriptionSource
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression

def generate_launch_description():
    bumperbot_description_dir = get_package_share_directory("bumperbot_description")
    ros_distro=os.environ.get("ROS_DISTRO") # tim ra phien ban ROS dang su dung, de tuong thich voi cac phien ban khac nhau
    is_ignition = "true" if ros_distro == "humble" else "false" # kiem tra xem co phai dang dung ROS2 Humble hay khong, de tuong thich voi cac phien ban khac nhau
    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(bumperbot_description_dir,
                                    "urdf", "bumperbot.urdf.xacro"),
        description="Truyền đường dẫn file urdf vào đây"
    )

    world_name_arg= DeclareLaunchArgument(
        name="world_name",
        default_value="empty",
        description="Tên file world"
    )

    world_path = PathJoinSubstitution([
        bumperbot_description_dir,
        "worlds",
        PythonExpression(["'", LaunchConfiguration('world_name'), ".world'"])
    ])

    model_path = str(Path(bumperbot_description_dir).parent.resolve())
    model_path += pathsep + os.path.join(bumperbot_description_dir, "models", "models")

    robot_description = ParameterValue(Command([
        "xacro ", 
        LaunchConfiguration("model"), " is_ignition:=", is_ignition]), value_type= str)

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}]
    )

    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ SIM RESOURCE PATH",
        value= model_path
    )

    ign_resource_path = SetEnvironmentVariable(
    name="IGN_GAZEBO_RESOURCE_PATH",
    value=model_path
    )

    gazebo = IncludeLaunchDescription(PythonLaunchDescriptionSource([
        os.path.join(
            get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
        launch_arguments={
            "gz_args":PythonExpression(["'", world_path, " -v 4 -r'"]) #-v (verbose) điều chỉnh mức độ thông tin 
                                                        # in ra terminal, -r (run) bắt đầu 
                                                        #chạy simulation ngay sau khi mở
        }.items()      
    )
    gz_spawn_entity = Node( # dùng để đẩy robot vào bên trong gazebo 
        package="ros_gz_sim",
        executable ="create", 
        output="screen",
        arguments=["-topic", "robot_description",
                  "-name", "bumperbot"]

    )

    gz_ros2_bridge = Node( # tao ra một bridge giữa ROS2 và Gazebo, để ROS2 có thể giao tiếp với Gazebo
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU"
        ],
        remappings=[
            ("/imu", "/imu/out")
        ]
    )
    return LaunchDescription([
        model_arg,
        world_name_arg,
        robot_state_publisher,
        gazebo_resource_path, ign_resource_path, gazebo,
        gz_spawn_entity,
        gz_ros2_bridge
    ])
'''
SetEnvironmentVariable được sử dụng để thiết lập biến môi trường bên trong Ros2
launch file , nó được sử dụng để cho gazebo biết nơi tìm tài nguyên của robot, ví
dụ như file URDF, mesh stl, ... 
* IncludeLaunchDescription: Để khởi động một file launch này trong file launch hiện
tại , ta cần import class IncludeLaunchDescription từ module launch.actions
'''



