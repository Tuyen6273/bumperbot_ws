#!/usr/bin/env bash
# Run from any directory. Does not install packages or launch hardware.
set -eo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo 'Cần cài ROS 2 Jazzy trước khi build.' >&2
  exit 1
fi
if [[ -n ${ROS_DISTRO:-} && ${ROS_DISTRO} != jazzy ]]; then
  echo 'Terminal đang source ROS khác. Mở terminal sạch, chỉ source Jazzy.' >&2
  exit 1
fi
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --symlink-install --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF "$@"
