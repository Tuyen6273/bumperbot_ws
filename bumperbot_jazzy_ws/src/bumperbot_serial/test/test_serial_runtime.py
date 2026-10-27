"""Exercise real ROS callbacks/launch and serial I/O using a pseudo-terminal.

Run after building and sourcing this package. No motor or USB device is used.
"""

import os
import pty
import re
import select
import signal
import subprocess
import time

import pytest

rclpy = pytest.importorskip('rclpy')
from geometry_msgs.msg import TwistStamped
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import Joy
import serial
from std_msgs.msg import String

from bumperbot_serial.protocol import STOP_PACKET


@pytest.fixture
def serial_runtime(tmp_path, monkeypatch, request):
    monkeypatch.setenv('ROS_DOMAIN_ID', str(140 + os.getpid() % 60))
    monkeypatch.setenv('ROS_LOCALHOST_ONLY', '1')
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'ros_logs'))
    master, slave = pty.openpty()
    path = os.ttyname(slave)
    os.set_blocking(master, False)
    log = open(tmp_path / 'launch.log', 'w+')
    process = subprocess.Popen([
        'ros2', 'launch', 'bumperbot_serial', 'serial_motor_test.launch.py',
        f'serial_port:={path}', 'startup_delay:=0.0',
        'cmd_vel_topic:=/standalone_serial_test/cmd_vel',
        f'start_joystick:={str(getattr(request, "param", False)).lower()}',
    ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    context = rclpy.context.Context()
    rclpy.init(context=context)
    node = rclpy.create_node('standalone_serial_test', context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(node)
    publisher = node.create_publisher(TwistStamped, '/standalone_serial_test/cmd_vel', 10)
    rx = []
    subscription = node.create_subscription(
        String, '/serial_motor_node/serial_rx', lambda msg: rx.append(msg.data), 10)
    state = dict(master=master, process=process, node=node, executor=executor, publisher=publisher,
                 log=log, rx=rx, subscription=subscription, path=path)
    try:
        deadline = time.monotonic() + 12
        while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
            assert process.poll() is None, 'Launch exited before ROS discovery'
            executor.spin_once(timeout_sec=0.05)
        assert publisher.get_subscription_count() == 1
        yield state
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        executor.shutdown()
        node.destroy_node()
        context.try_shutdown()
        os.close(slave)
        try:
            os.close(master)
        except OSError:
            pass
        log.seek(0)
        print(log.read())
        log.close()


def packets(runtime, duration):
    buffer = b''
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        runtime['executor'].spin_once(timeout_sec=0.01)
        if select.select([runtime['master']], [], [], 0.01)[0]:
            buffer += os.read(runtime['master'], 65536)
    return re.findall(rb'r[pn]\d{2}\.\d{2},l[pn]\d{2}\.\d{2},', buffer)


def publish(runtime, linear, angular=0.0, age=0.0, zero_stamp=False):
    message = TwistStamped()
    if not zero_stamp:
        stamp = runtime['node'].get_clock().now().nanoseconds - int(age * 1e9)
        message.header.stamp.sec = stamp // 1_000_000_000
        message.header.stamp.nanosec = stamp % 1_000_000_000
    message.twist.linear.x = linear
    message.twist.angular.z = angular
    runtime['publisher'].publish(message)


def test_ros_serial_motion_watchdog_rx_and_sigint(serial_runtime):
    runtime = serial_runtime
    assert STOP_PACKET in packets(runtime, 0.2)
    with pytest.raises(serial.SerialException, match='exclusively lock'):
        serial.Serial(runtime['path'], exclusive=True)
    os.write(runtime['master'], b'rp01.23,ln02.34,\n')
    for _ in range(4):
        publish(runtime, 1.0)  # Driver must clamp this to 0.10 m/s.
        received = packets(runtime, 0.08)
        assert b'rp02.94,lp02.94,' in received
    assert any('rp01.23' in chunk for chunk in runtime['rx'])
    packets(runtime, 0.3)
    assert set(packets(runtime, 0.15)) == {STOP_PACKET}

    for kwargs in ({'age': 1.0}, {'zero_stamp': True}, {'age': -1.0}):
        publish(runtime, 0.05, **kwargs)
        assert set(packets(runtime, 0.12)) == {STOP_PACKET}

    # SIGINT while moving must put a final stop packet on the wire and exit promptly.
    publish(runtime, -0.05)
    assert b'rn01.47,ln01.47,' in packets(runtime, 0.08)
    os.killpg(runtime['process'].pid, signal.SIGINT)
    runtime['process'].wait(timeout=4)
    received = packets(runtime, 0.1)
    assert received and received[-1] == STOP_PACKET
    assert runtime['process'].returncode == 0


def test_serial_disconnect_exits_instead_of_retrying_motion(serial_runtime):
    runtime = serial_runtime
    packets(runtime, 0.1)
    os.close(runtime['master'])
    runtime['process'].wait(timeout=4)
    runtime['log'].flush()
    runtime['log'].seek(0)
    output = runtime['log'].read()
    assert 'Serial I/O failed:' in output
    assert 'exit code 1' in output


@pytest.mark.parametrize('serial_runtime', [True], indirect=True)
def test_joystick_deadman_stamped_commands_and_launch_cleanup(serial_runtime):
    runtime = serial_runtime
    publisher = runtime['node'].create_publisher(Joy, '/joy', 10)
    deadline = time.monotonic() + 8
    while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
        runtime['executor'].spin_once(timeout_sec=0.05)
    assert publisher.get_subscription_count() == 1
    packets(runtime, 0.15)
    message = Joy()
    message.axes = [0.0, 0.5, 0.0, 0.0]
    message.buttons = [0, 0, 0, 0, 0, 1]
    for _ in range(3):
        message.header.stamp = runtime['node'].get_clock().now().to_msg()
        publisher.publish(message)
        assert b'rp01.47,lp01.47,' in packets(runtime, 0.08)
    message.buttons[5] = 0
    message.header.stamp = runtime['node'].get_clock().now().to_msg()
    publisher.publish(message)
    packets(runtime, 0.1)
    assert set(packets(runtime, 0.1)) == {STOP_PACKET}
    # Driver loss must also stop the optional joystick processes via launch.
    os.close(runtime['master'])
    runtime['process'].wait(timeout=4)
    runtime['log'].flush()
    runtime['log'].seek(0)
    output = runtime['log'].read()
    assert 'Serial I/O failed:' in output
    assert 'sending signal' in output
