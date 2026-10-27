# Rà soát workspace Humble → Jazzy/Pi 5

Ngày rà soát: 14/10/2026. Đã xem 9 package ROS, các launch/config/URDF,
bản C++ thực sự được CMake build, các script Python, test hiện có, các firmware
Arduino/ESP32 và các đường dẫn tài nguyên. Build/install/log gốc được xem là
sản phẩm của Humble, không phải mã nguồn để chuyển. Mesh/texture/PDF được giữ
nguyên; kiểm tra cấu trúc/tài nguyên không có nghĩa đã kiểm nghiệm physics.

## Kết quả theo package

| Package/phần | Kết luận và cách xử lý |
|---|---|
| `bumperbot_msgs` | Hai service không đổi định nghĩa. Sửa `geometry_msg` thành `geometry_msgs`, cần cho rosdep và thứ tự dependency. |
| `bumperbot_controller` | Python đã dùng `TwistStamped`, API rclpy/tf2 và NumPy cơ bản; giữ nguyên động học, noise, odometry. Thêm YAML cho tất cả spawner, khai báo các controller plugin phải có trên Pi mới. |
| `bumperbot_firmware` | Theo lựa chọn người dùng, đổi đúng một đường dẫn CMake sang bản serial/encoder trong `include/`. Sửa vùng nhớ vector và return/header. Launch lấy URDF qua topic, ghi đè clock thật sau YAML. Giữ SMBus, baud/giao thức và thuật toán đọc/ghi. |
| `bumperbot_description` | Đã có nhánh `is_ignition=false` cho Gazebo Sim; không cần chuyển từ Gazebo Classic. Sửa tên thư viện gz và biến resource path, thêm bridge clock. Không sửa hình học/inertia/mesh/world. |
| `bumperbot_bringup` | Bỏ lần mở MPU6050 thứ hai ở real launch. Simulated launch đặt thời gian mô phỏng chung. Khai báo các package mà launch gọi. |
| `bumperbot_localization` | Giữ nguyên Kalman và EKF. Bổ sung dependency launch/tf2; không đổi noise, covariance, topic, frame hay mô hình fusion. |
| `bumperbot_serial` | Logic giao tiếp/giới hạn/watchdog Python đã phù hợp; không sửa. Chỉ bỏ dependency `ament_python` không có rosdep rule, vẫn giữ `<build_type>ament_python</build_type>`. |
| `bumberbot_py_examples` | Giữ tên package viết như bản gốc. Sửa rosdep key pygame và thêm YAML cho spawner trong launch joystick. Các bài học Python giữ nguyên, gồm cả lỗi gốc được ghi bên dưới. |
| `bumperbot_utils` | Rclpy, Odometry, Path không có điểm bắt buộc đổi được tìm thấy; giữ nguyên toàn package. |
| Firmware `.ino`, ESP32/UDP, script thử serial ở gốc | Không chạy ROS trên vi điều khiển; đổi distro của Pi không tự đòi đổi các file này. Giữ nguyên, chưa nạp/biên dịch firmware cho board cụ thể. |
| `documents`, `Untitled Document 1`, RViz/world/model/photos | Giữ nội dung làm tài liệu/tài nguyên tham khảo. Các lệnh/path cũ trong ghi chú không phải hướng dẫn triển khai Jazzy; dùng README mới. |

## Những thay đổi thật sự do Jazzy

**Controller YAML:** ở Humble file truyền vào manager có thể được controller
nhận qua global arguments; Jazzy tắt cơ chế này. Mọi spawner của cả hai launch
phải nhận `--param-file`. Không đổi giá trị bán kính, khoảng cách bánh hoặc gain.

**Robot description:** `ros2_control_node` nhận topic `robot_description`.
`robot_state_publisher` vẫn nhận parameter `robot_description` như trước và
phát topic. Vì vậy chỉ bỏ parameter ở manager, không bỏ ở publisher.
Nguồn: [migration ros2_control](https://control.ros.org/jazzy/doc/ros2_control/doc/migration.html).

**TwistStamped:** diff_drive_controller Jazzy yêu cầu lệnh stamped, nhưng
joystick, simple controller và serial node trong workspace đã đáp ứng.
Không thêm bridge Twist → TwistStamped không cần thiết.
Nguồn: [migration controllers](https://control.ros.org/jazzy/doc/ros2_controllers/doc/migration.html).

**Gazebo:** Jazzy dùng Harmonic với `gz_ros2_control`. Chỗ cũ viết
`gz_ros2_control_system` không khớp tên thư viện `gz_ros2_control-system`.
`GZ SIM RESOURCE PATH` cũng không phải biến mà Gazebo đọc. Đây là lỗi cấu hình
đã có, lộ rõ khi dùng nhánh gz. Thêm `/clock` và đồng bộ các node để timestamp
joystick, odometry và controller không trộn wall time với simulation time.
Nguồn: [plugin](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html),
[CMake khai báo thư viện](https://raw.githubusercontent.com/ros-controls/gz_ros2_control/jazzy/gz_ros2_control/CMakeLists.txt).

## Những thứ không bắt buộc sửa chỉ để dùng Jazzy

- Không thay toàn bộ `on_init(HardwareInfo)` hoặc `export_*_interfaces()` bằng
  API mới. Nhánh Jazzy vẫn giữ các API cũ (có thể cảnh báo deprecated); đổi toàn
  bộ vùng nhớ/handle lúc này sẽ làm diff lớn mà không cần thiết. Đã đối chiếu
  [header chính thức nhánh Jazzy](https://raw.githubusercontent.com/ros-controls/ros2_control/jazzy/hardware_interface/include/hardware_interface/hardware_component_interface.hpp).
- Không đổi toàn bộ `setup.py` sang công cụ khác hoặc viết lại CMake vì Python
  3.12. Cần build lại message/binding bằng Python của Jazzy, không chép `.so`
  hoặc `.pyc` Python 3.10 từ Humble.
- Không đổi thư viện điều khiển GPIO cho Pi 5: driver hiện có dùng USB serial
  và `/dev/i2c-1` qua `smbus`; không dùng RPi.GPIO hay truy cập thanh ghi GPIO.
- Không đổi các node sang C++ chỉ vì máy là Pi; chưa có đo đạc cho thấy cần.
- Không tự thay EKF/Kalman, tốc độ vòng lặp, deadzone, giới hạn tốc độ hay PID.
- YAML vẫn giữ các khóa cũ `use_stamped_vel`, `publish_wheel_data` và
  `has_*_limits`. Hai khóa đầu không điều khiển tính năng tương ứng ở Jazzy;
  stamped luôn bắt buộc. Các cờ giới hạn đang được nhánh Jazzy giữ để tương
  thích/deprecate; giới hạn velocity/acceleration hữu hạn vẫn giữ nguyên,
  jerk không có giá trị hữu hạn. Không coi việc xóa các khóa bị bỏ qua là
  điều kiện bắt buộc để robot chạy. Schema tham chiếu:
  [diff_drive_controller Jazzy](https://raw.githubusercontent.com/ros-controls/ros2_controllers/jazzy/diff_drive_controller/src/diff_drive_controller_parameter.yaml).
  Nếu sau này distro/version báo lỗi deprecated, kiểm tra schema của bản cài
  trước khi sửa; không tự thay các con số giới hạn.

## Lỗi gốc đã sửa vì cản trở đường chạy được chọn

1. CMake trỏ tới file `src/bumperbot_interface.cpp`: `read`/`write` chỉ trả OK,
   không giao tiếp; file đó cũng không có `PLUGINLIB_EXPORT_CLASS`.
   Bản trong `include/` đã có thuật toán serial và macro export. Người dùng
   đã chọn dùng bản này. File stub vẫn được giữ để có thể đối chiếu.
2. `reserve()` chỉ đặt capacity, không tạo phần tử. Export interface xảy ra
   trước activate, nên lấy `&vector[i]` lúc size bằng 0 là truy cập không hợp lệ.
   `resize(..., 0.0)` tạo đúng vùng nhớ; không thay dữ liệu đo hay công thức.
3. `on_deactivate()` thiếu return thành công gây hành vi không xác định.
4. File driver sử dụng stream/format/math nhưng thiếu header trực tiếp.
5. YAML `use_sim_time: true` được truyền sau dictionary `false` ở launch robot
   thật. Đảo thứ tự để giá trị cuối cùng đúng cho Pi.
6. `real_robot.launch.py` include hardware launch đã mở IMU rồi lại mở thêm.
7. Các dependency sai tên hoặc thiếu làm máy đã cài nhiều gói có thể chạy,
   nhưng một Pi mới cài không thể tái tạo môi trường chỉ bằng rosdep.

Các mục này **không được gọi nhầm là thay đổi API Humble → Jazzy**.

## Giới hạn/lỗi sẵn có được giữ, ngoài phạm vi chuyển tối thiểu

- `simple_publisher.py` gọi `self.timer_callback(1, self.timer_callback)` thay
  vì tạo timer; bài học này vẫn lỗi khi chạy. `param_examples.py` dùng
  `param.type` ở một nhánh thay vì `param.type_`. Không sửa bài học trong
  công việc chuyển distro cho robot; build thành công không chứng minh các
  executable ví dụ đều chạy đúng.
- `noisy_controller.py` và `simple_controller.py` đều đặt tên node
  `simple_controller`; nhánh simple có thể trùng tên. Chúng dùng vị trí joint
  theo index (0 phải, 1 trái), không theo tên và không xử lý dt=0. Không đổi
  thuật toán; khi kiểm tra Pi phải đối chiếu `JointState.name` với thứ tự này.
- EKF lấy `odom_noisy`; MPU6050 chỉ đo acceleration/gyro, không tính quaternion
  orientation. `imu_republisher` chỉ đổi frame_id, không xoay vector. Đây là
  mô hình bài học, chưa phải xác nhận chất lượng định vị robot thật.
- Driver C++ `ReadLine()` có thể chờ khi feedback thiếu newline; parser không
  chịu được mọi dòng hỏng/chuỗi khởi động. Không có watchdog độc lập trong
  driver/firmware được chọn. Test serial giả lập chỉ xác nhận giao thức hợp lệ,
  không xác nhận an toàn mất nguồn/đứt dây hoặc hệ thống điều khiển thời gian thực.
- Firmware `robot_control.ino` có pin/PPR/PID theo phần cứng gốc; chẳng hạn pin
  24 phải được đối chiếu với board thật, không tự suy đoán board Arduino/ESP32.
  Bản UDP dùng PWM, không dùng giao thức rad/s của driver C++.
- Giọng nói (`gemini_voice_controller.py`, thực tế import Groq) cần dịch vụ
  ngoài, microphone, `groq`/`sounddevice`; chúng không phải dependency của
  bringup motor. Có thông tin xác thực hard-code trong source gốc; không đưa
  giá trị đó vào báo cáo hay diff. Bản sao giữ nguyên theo yêu cầu; không chia
  sẻ công khai workspace chứa thông tin này. Chưa gọi dịch vụ hoặc thử API key.
- Các file voice/test trống, `check_signal.py`, các sketch thử encoder/LED là
  tài liệu thực hành; không tự viết thêm chức năng.

Với chức năng giọng nói tùy chọn trên Ubuntu 24.04, dùng môi trường Python
riêng nếu cần cài dependency bằng pip (không cài đè Python hệ thống). Cấu hình
microphone/IP/API là việc triển khai ứng dụng, không phải sửa bắt buộc cho Jazzy.

## Máy đang kiểm tra và máy đích

Máy hiện tại: Ubuntu 22.04.5 x86_64, `/opt/ros/humble`; không có Jazzy,
Raspberry Pi, USB motor hoặc IMU để kiểm tra trực tiếp. Kiểm tra dependency
sử dụng danh sách release Jazzy/rosdep chính thức; việc một key tồn tại không
bằng việc apt đã cài thành công binary ARM64 trên máy đích.

Các file tham chiếu chính thức và SHA256 tại thời điểm rà soát nằm trong
`reference_sources.json`. Luôn xem `VALIDATION.md` trước khi diễn giải chữ
“đã kiểm tra”. Các bước Pi còn lại là bước nghiệm thu thực tế, không phải kết
quả đã được thực hiện trong lần này.
