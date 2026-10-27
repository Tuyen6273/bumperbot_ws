# Danh sách thay đổi có thể đối chiếu

Có **17 / 611 file gốc** đổi nội dung; 594 file được giữ nguyên từng byte.

Các file mới trong `tools/` và `migration/`, README và COLCON_IGNORE phục vụ kiểm tra/tài liệu; không được thêm vào logic điều khiển.

Diff đầy đủ: [changes.patch](changes.patch). Bản gốc từng file sửa: `baseline/`.


## `src/bumberbot_py_examples/launch/controller_joystick.launch.py`

- Jazzy: tìm đường dẫn YAML cho spawner.

- Jazzy: controller không kế thừa global arguments của manager.

- Jazzy: truyền YAML trực tiếp cho từng spawner.


## `src/bumberbot_py_examples/package.xml`

- Dùng đúng rosdep key cho pygame Python 3.

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_bringup/launch/real_robot.launch.py`

- Lỗi gốc: IMU đã được khởi động bởi hardware launch; tránh chạy hai driver cùng I2C.

- Bỏ IMU trùng; vẫn giữ một driver trong hardware launch.


## `src/bumperbot_bringup/launch/simulated_robot.launch.py`

- Đồng bộ clock của các node launch cùng mô phỏng.

- Joystick và các controller Python dùng chung thời gian Gazebo.


## `src/bumperbot_bringup/package.xml`

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_controller/launch/controller.launch.py`

- Jazzy: tìm đường dẫn YAML cho spawner.

- Jazzy: controller không kế thừa global arguments của manager.

- Jazzy: truyền YAML trực tiếp cho từng spawner.


## `src/bumperbot_controller/package.xml`

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_description/launch/gazebo.launch.py`

- Harmonic đọc biến môi trường này để tìm mesh/model.

- Đồng bộ timestamp của robot_state_publisher với mô phỏng.

- Mô phỏng: cấp clock cho các node dùng use_sim_time.


## `src/bumperbot_description/package.xml`

- Sửa tên package bridge bị sai.

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_description/urdf/bumperbot_gazebo.urdf.xacro`

- Jazzy/Harmonic: đúng tên thư viện plugin (dấu gạch ngang).


## `src/bumperbot_firmware/CMakeLists.txt`

- Theo lựa chọn người dùng: build driver serial/encoder hiện có thay vì bản stub.


## `src/bumperbot_firmware/include/bumperbot_firmware/bumperbot_interface.cpp`

- Bổ sung header trực tiếp cho các hàm đã có trong driver được chọn.

- Lỗi gốc: reserve không tạo phần tử; phải có vùng nhớ hợp lệ trước export interfaces.

- Lỗi gốc: on_deactivate thiếu return khi thành công.


## `src/bumperbot_firmware/launch/hardware_interface.launch.py`

- Jazzy: manager nhận URDF qua topic; robot thật ghi đè use_sim_time sau YAML.


## `src/bumperbot_firmware/package.xml`

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_localization/package.xml`

- Khai báo dependency thực sự được import/chạy để rosdep cài đủ trên máy mới.


## `src/bumperbot_msgs/package.xml`

- Sửa tên dependency có sẵn bị sai; chặn rosdep trên máy mới.


## `src/bumperbot_serial/package.xml`

- Lỗi gốc: ament_python là build_type, không phải dependency rosdep; giữ export/build_type, bỏ buildtool_depend không tồn tại.

## Bổ sung sau khi kiểm tra launch trên Pi

Ba file chỉ đổi quyền thực thi, không đổi nội dung: `Mpu6050.py`, `kalman_filter.py`, `imu_republisher.py`. Build với `--symlink-install` giữ quyền file nguồn; ROS cần bit `x` để tìm executable. Diff nội dung vẫn có 17 file; đổi quyền được ghi trong `original_exec_bits.json` và `delivered_exec_bits.json`. `check_changes.py` giờ kiểm tra cả quyền thực thi.
