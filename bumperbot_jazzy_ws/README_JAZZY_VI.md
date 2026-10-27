# Bumperbot: bản chuyển tối thiểu sang ROS 2 Jazzy trên Raspberry Pi 5

Bản này giữ nguyên các node điều khiển Python, công thức động học, Kalman/EKF,
kích thước robot, mapping tay cầm và firmware vi điều khiển. Mã nguồn gốc ở
workspace cha không bị sửa. **Chưa xác nhận chạy trên Jazzy/Pi hoặc motor thật**;
xem kết quả thực tế trong [VALIDATION.md](migration/VALIDATION.md).

Mục tiêu hệ thống: **Ubuntu 24.04 64-bit (ARM64) + ROS 2 Jazzy trên Pi 5**.
Không dùng các lệnh apt Jazzy/Ubuntu này trực tiếp cho Raspberry Pi OS/Debian.
Jazzy có binary cho Ubuntu Noble/ARM64; xem
[tài liệu cài đặt chính thức](https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Installation/Ubuntu-Install-Debs.rst).

## 1. Đọc những gì trước?

- [AUDIT_VI.md](migration/AUDIT_VI.md): rà soát từng package, lý do sửa và các lỗi gốc còn giữ.
- [CHANGES_VI.md](migration/CHANGES_VI.md): danh sách từng file đã thay đổi.
- [changes.patch](migration/changes.patch): diff chính xác so với bản gốc.
- [VALIDATION.md](migration/VALIDATION.md): đã kiểm tra gì, chưa kiểm tra gì.

Workspace mới đang nằm **bên trong** workspace cũ để dễ giữ và đối chiếu.
File `COLCON_IGNORE` ở gốc bản mới tránh cho `colcon` ở workspace cha tìm thấy
hai bản của cùng package. Vì vậy trong bản mới luôn dùng `--base-paths src`.
Script `tools/build_jazzy.sh` đã làm việc này. Có thể chuyển toàn bộ thư mục
`bumperbot_jazzy_ws` ra `~/bumperbot_jazzy_ws` trên Pi; cấu trúc source độc lập.

## 2. Các thay đổi cốt lõi

| Việc | Tại sao cần | Có đổi thuật toán không? |
|---|---|---|
| Truyền `--param-file` cho các spawner | Jazzy không cho controller kế thừa global arguments của manager | Không |
| Manager nhận URDF qua `/robot_description` | Giao diện nạp URDF của Jazzy | Không |
| Đặt `use_sim_time: false` sau YAML ở launch robot thật | YAML gốc đang ghi đè về `true`, trong khi Pi không có `/clock` | Không |
| Build file driver hiện có trong `include/` | Theo lựa chọn của bạn; file trong `src/` là stub, thiếu cả export macro | Dùng đúng thuật toán đã có |
| `reserve` → `resize`, thêm header, return lifecycle | Sửa lỗi khởi tạo/biên dịch của driver được chọn | Không |
| Bỏ một lần khởi động MPU6050 trùng | Launch cũ mở hai node trên cùng I2C | Không |
| Sửa tên và khai báo dependency thiếu | `rosdep` trên máy mới cần đúng tên gói | Không |
| Sửa tên plugin/resource path và bridge clock mô phỏng | Chạy nhánh Gazebo Harmonic của Jazzy | Không |

Các thay đổi spawner/URDF dựa trên
[hướng dẫn ros2_control Humble → Jazzy](https://control.ros.org/jazzy/doc/ros2_control/doc/migration.html).
Phần mô phỏng dùng [gz_ros2_control với Harmonic](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html).

## 3. Chép và build trên Pi

Chép **cả thư mục mới** vào `~/bumperbot_jazzy_ws` trên Pi. Nếu dùng gói
`bumperbot_jazzy_ws.tar.gz`, giải nén trên Pi bằng
`tar -xzf ~/Downloads/bumperbot_jazzy_ws.tar.gz -C ~` (khi chưa có thư mục
đích cùng tên). Không chép `build`,
`install`, `log` của máy Humble/x86_64. Chúng chứa binary, đường dẫn và module
Python theo máy/ROS cũ. Bản bàn giao đã loại cả các thư mục build lồng trong `src`.

Sau khi cài Jazzy theo hướng dẫn chính thức, mở terminal không source Humble
hoặc workspace Humble trong `.bashrc`. Thực hiện trên Pi:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-dev-tools python3-pytest
# Chỉ chạy sudo rosdep init nếu máy chưa từng khởi tạo rosdep:
sudo rosdep init
rosdep update
cd ~/bumperbot_jazzy_ws
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
CMAKE_BUILD_PARALLEL_LEVEL=2 ./tools/build_jazzy.sh
source install/setup.bash
colcon list --base-paths src
```

`rosdep init` báo đã tồn tại thì bỏ qua bước đó, không xoá cấu hình hiện có.
Script dùng `--executor sequential`; biến CMake trên giới hạn số luồng compile
trong mỗi package để giảm RAM trên Pi. `BUILD_TESTING=OFF` chỉ bỏ test/lint khỏi
bước build ứng dụng; không chứng minh test đã qua.

Lệnh cài dependency toàn workspace cũng kéo Gazebo/RViz vì chúng đã nằm trong
package description ban đầu. Không phải khởi chạy chúng khi chạy robot thật.
Để chỉ thử serial trước, có thể dùng cách nhẹ hơn:

```bash
rosdep install --from-paths src/bumperbot_serial --ignore-src --rosdistro jazzy -y
CMAKE_BUILD_PARALLEL_LEVEL=2 ./tools/build_jazzy.sh --packages-select bumperbot_serial
source install/setup.bash
```

## 4. Chạy robot thật qua ros2_control

Driver được chọn dùng serial 115200, lệnh dạng `rp01.00,ln02.50,`, feedback
encoder dạng `rp1.25,ln2.50,` kết thúc bằng newline. Đây là giao thức của
`src/bumperbot_firmware/firmware/robot_control/robot_control.ino`; mã ESP32 Wi-Fi
nhận UDP/PWM là một đường điều khiển khác, không tự tương thích với driver này.
Không có thao tác nạp firmware nào được thực hiện trong lần chuyển workspace.

Trước khi chạy, kiểm tra thiết bị trên Pi:

```bash
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/i2c-*
groups
```

URDF vẫn giữ cổng gốc `/dev/ttyUSB0`, dự phòng `/dev/ttyACM0`. Nếu máy của bạn
khác, sửa đúng hai giá trị `port`/`fallback_port` trong
`src/bumperbot_description/urdf/bumperbot_ros2_control.xacro`, rồi build lại.
Có thể dùng đường dẫn `/dev/serial/by-id/...` ổn định sau khi xác nhận tên thật.
Quyền serial thường qua nhóm `dialout`; nếu chưa có, dùng
`sudo usermod -aG dialout "$USER"` rồi đăng xuất/đăng nhập.

MPU6050 vẫn dùng SMBus **bus 1, địa chỉ 0x68**. Bật I2C trên hệ điều hành Pi,
kiểm tra có `/dev/i2c-1` và quyền truy cập. Chỉ khi bus thật khác mới sửa bus
trong `Mpu6050.py`; không cần thay thư viện chỉ vì chuyển từ Humble sang Jazzy.
Không thêm driver GPIO cho Pi 5 vì workspace này không dùng `RPi.GPIO`.

Kê bánh khi thử chiều quay lần đầu, dừng chương trình khác đang giữ serial, rồi:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bumperbot_jazzy_ws/install/setup.bash
ros2 launch bumperbot_bringup real_robot.launch.py
```

Terminal khác, kiểm tra trước khi gửi vận tốc:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bumperbot_jazzy_ws/install/setup.bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 param get /controller_manager use_sim_time
ros2 topic info /bumperbot_controller/cmd_vel -v
ros2 topic echo /joint_states --once
```

Kỳ vọng `joint_state_broadcaster` và `bumperbot_controller` đều `active`,
`use_sim_time` là `False`, topic vận tốc là `geometry_msgs/msg/TwistStamped`.
Thử lệnh 0 trước:

```bash
ros2 topic pub -r 20 /bumperbot_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{header: auto, twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'
```

Sau khi xác nhận firmware/cổng/chiều quay, thay `x: 0.0` bằng `x: 0.03` để
thử chậm. Joystick launch gốc đã chạy cùng real_robot; không đồng thời điều
khiển bằng joystick và publisher thử. `cmd_vel_timeout` vẫn là 0,25 giây.
Driver C++ gốc không có watchdog vi điều khiển hay xác nhận dừng khi mất USB;
đây là giới hạn hiện có, không được tự thiết kế lại trong bản chuyển tối thiểu.

Nếu chỉ cần thử truyền lệnh serial, dùng `bumperbot_serial` theo
[README của package](src/bumperbot_serial/README.md), thay đường dẫn workspace
trong ví dụ bằng `~/bumperbot_jazzy_ws`. **Không chạy đồng thời** với driver
C++ trên cùng cổng. Nhánh serial riêng chưa cung cấp encoder odometry/TF.

## 5. Mô phỏng và localization

Chạy mô phỏng trên máy cài Jazzy/Harmonic (có thể là PC để giảm tải Pi):

```bash
ros2 launch bumperbot_bringup simulated_robot.launch.py
ros2 topic echo /clock --once
```

Launch tổng đồng bộ `use_sim_time` cho joystick và các node Python. File
`gazebo.launch.py` đã bridge `/clock`. Chưa xác nhận GUI, physics, các world
`small_house`/`small_warehouse` trên Pi; tài nguyên được giữ nguyên từng byte.
Nếu khởi chạy các launch riêng ở các terminal riêng, phải tự đồng bộ
`use_sim_time` cho tất cả các node liên quan.

Local localization không nằm trong launch tổng gốc. Khi cần cho robot thật:

```bash
ros2 launch bumperbot_localization local_localization.launch.py
```

Giữ nguyên mô hình EKF phục vụ bài học: đầu vào là `odom_noisy`, không tự đổi
sang odometry thật hay chỉnh covariance. Xem các giới hạn IMU/EKF trong audit.

## 6. Tự kiểm soát thay đổi

```bash
cd ~/bumperbot_jazzy_ws
less migration/changes.patch
python3 tools/check_changes.py
# Trên máy gốc, xác nhận các file gốc chưa thay đổi:
python3 tools/check_changes.py --original /home/tuyen/bumperbot_ws
```

Mỗi lần bạn sửa tiếp, `check_changes.py` báo file khác với bản bàn giao.
Nó kiểm tra nội dung các file đã ghi trong manifest; không kiểm tra file mới
phát sinh. `migration/original_sha256.json` giữ dấu vết bản gốc, còn
`delivered_sha256.json` giữ dấu vết bản đã chuyển. `migration/baseline/` chứa
bản gốc của riêng những file có sửa, để mở cạnh nhau trong editor.

Có thể kiểm tra khả năng hoàn tác diff mà chưa sửa file:

```bash
patch --dry-run -R -p1 < migration/changes.patch
```

Diff không chứa build output hoặc thay đổi mesh; khôi phục bản gốc sẽ khôi
phục cả các lỗi cũ và không còn các điều chỉnh Jazzy.

## Nếu nhận bản trước và launch báo Mpu6050.py not found

Trên Pi, cấp quyền cho ba script nguồn rồi source lại. Với symlink-install, không cần build lại chỉ để cập nhật bit thực thi:

```bash
cd ~/bumperbot_jazzy_ws
chmod +x src/bumperbot_firmware/bumperbot_firmware/Mpu6050.py
chmod +x src/bumperbot_localization/bumperbot_localization/{kalman_filter,imu_republisher}.py
source install/local_setup.bash
ros2 pkg executables bumperbot_firmware
```
