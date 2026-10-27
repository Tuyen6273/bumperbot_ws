from launch import LaunchDescription
from launch_ros.actions import SetParameter
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription

def generate_launch_description():
    description_pkg_path = get_package_share_directory('bumperbot_description')
    controller_pkg_path = get_package_share_directory('bumperbot_controller')

    gazebo = IncludeLaunchDescription(
        os.path.join(description_pkg_path, 
                     'launch', 'gazebo.launch.py')
    )

    controller = IncludeLaunchDescription(
        os.path.join(controller_pkg_path, 
                     'launch', 'controller.launch.py'
        ),
        launch_arguments= {
            "use_simple_controller": "False",
        }.items()
    )

    joystick = IncludeLaunchDescription(
            os.path.join(controller_pkg_path, 
                         'launch', 'joystick_teleop.launch.py')
    )

    return LaunchDescription([
        SetParameter(name="use_sim_time", value=True),
        gazebo,
        controller,
        joystick,
    ])