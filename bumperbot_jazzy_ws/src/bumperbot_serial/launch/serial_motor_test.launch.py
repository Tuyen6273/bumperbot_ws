"""Launch the standalone serial driver, optionally with joystick control."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    arguments = [
        ('serial_port', '/dev/ttyUSB0', 'USB serial path, preferably /dev/serial/by-id/...'),
        ('baud_rate', '115200', 'Firmware serial baud rate'),
        ('cmd_vel_topic', '/bumperbot_controller/cmd_vel', 'Input TwistStamped topic'),
        ('start_joystick', 'false', 'Start joy and teleop_twist_joy'),
        ('wheel_radius', '0.034', 'Wheel radius in metres'),
        ('wheel_separation', '0.2565', 'Distance between wheels in metres'),
        ('max_linear_velocity', '0.10', 'Maximum body speed in m/s'),
        ('max_angular_velocity', '0.50', 'Maximum body yaw speed in rad/s'),
        ('max_wheel_velocity', '5.0', 'Maximum wheel speed in rad/s'),
        ('command_timeout', '0.25', 'Stop after this many seconds without a fresh command'),
        ('send_rate', '20.0', 'Serial command frequency in Hz'),
        ('startup_delay', '2.0', 'Wait for the microcontroller after opening serial'),
        ('left_direction', '1', 'Set -1 to reverse the left motor command'),
        ('right_direction', '1', 'Set -1 to reverse the right motor command'),
    ]
    parameters = {}
    for name, _, _ in arguments:
        if name == 'start_joystick':
            continue
        parameter_type = str if name in ('serial_port', 'cmd_vel_topic') else (
            int if name in ('baud_rate', 'left_direction', 'right_direction') else float)
        parameters[name] = ParameterValue(LaunchConfiguration(name), value_type=parameter_type)
    parameters['use_sim_time'] = False
    serial_node = Node(
        package='bumperbot_serial', executable='serial_motor_node',
        output='screen', parameters=[parameters])
    joystick_config = os.path.join(
        get_package_share_directory('bumperbot_serial'), 'config', 'joystick.yaml')
    joystick = Node(
        package='joy', executable='joy_node', name='serial_joystick', output='screen',
        parameters=[joystick_config], condition=IfCondition(LaunchConfiguration('start_joystick')))
    teleop = Node(
        package='teleop_twist_joy', executable='teleop_node', name='serial_teleop',
        output='screen', parameters=[joystick_config],
        remappings=[('cmd_vel', LaunchConfiguration('cmd_vel_topic'))],
        condition=IfCondition(LaunchConfiguration('start_joystick')))
    return LaunchDescription([
        *[DeclareLaunchArgument(name, default_value=default, description=description)
          for name, default, description in arguments],
        RegisterEventHandler(OnProcessExit(
            target_action=serial_node,
            on_exit=[EmitEvent(event=Shutdown(reason='Serial motor driver exited'))])),
        serial_node, joystick, teleop,
    ])
