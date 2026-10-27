#!/usr/bin/env bash
# Read-only against real hardware: URDF/static checks and pseudo-terminal tests.
set -eo pipefail
cd "$(dirname "$0")/.."
if [[ ${ROS_DISTRO:-} != jazzy ]]; then
  echo 'Mở terminal sạch và source /opt/ros/jazzy/setup.bash trước.' >&2
  exit 1
fi
if [[ ! -f install/local_setup.bash ]]; then
  echo 'Build workspace trước bằng tools/build_jazzy.sh.' >&2
  exit 1
fi
source install/local_setup.bash
python3 tools/validate_source.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest src/bumperbot_serial/test -q
cmake -S tools/hardware_probe -B build/hardware_probe
cmake --build build/hardware_probe -j2
timeout 15 build/hardware_probe/hardware_probe
ros2 launch bumperbot_bringup real_robot.launch.py --show-args
printf '%s\n' 'PASS: kiểm tra phần mềm trên Jazzy; chưa xác nhận motor, IMU hoặc Gazebo.'
