# Kết quả kiểm tra — 14/10/2026

**Chưa build/chạy trên ROS 2 Jazzy, ARM64 hoặc Raspberry Pi 5.** Môi trường
kiểm tra hiện có là Ubuntu 22.04.5 x86_64, ROS 2 Humble, Python 3.10.
Không nối tới motor, IMU, ESP32 hoặc dịch vụ giọng nói trong các kiểm tra này.

| Kiểm tra | Kết quả thực tế |
|---|---|
| Build 9 package với colcon, thư mục build/install riêng trong `/tmp` | PASS. Driver C++ còn cảnh báo tham số chưa dùng; không có lỗi compile/link. `BUILD_TESTING=OFF`. |
| Test sẵn có `bumperbot_serial/test` | **12 passed** khi chạy ngoài sandbox. Bao gồm ROS → serial giả lập, giới hạn, timestamp, watchdog, RX, SIGINT, khóa cổng, disconnect và joystick. |
| Probe driver C++ được chọn qua pluginlib + pseudo-terminal | PASS: plugin load, export trước activate, fallback cổng, đúng chuỗi TX, nhận encoder CRLF, tích phân vị trí và deactivate. |
| Parse Python/YAML/XML | PASS: 51 file Python trong src, 5 YAML, 180 XML/Xacro/SDF/world/config. Không đồng nghĩa mọi executable ví dụ đúng logic. |
| Expand Xacro với `is_sim=false` và `is_sim=true`, `is_ignition=false` | PASS: đúng hardware plugin, hai joint có trong URDF, mesh tồn tại. |
| `--show-args` cho real_robot, simulated_robot, controller_joystick | PASS trên Humble; chỉ kiểm tra khả năng dựng launch, không chạy các node đó. |
| Dependency đối chiếu danh sách release Jazzy + rosdep chính thức | Tất cả key đang áp dụng cho Jazzy đều tồn tại; chưa thực hiện `rosdep install`/apt ARM64 trên Pi. |
| SHA256 mã nguồn/tài nguyên gốc | Kiểm tra bằng `tools/check_changes.py --original ...`; không thay đổi nội dung 611 file gốc được sao chép. |
| Đối chiếu diff và hoàn tác khô | `patch --dry-run -R -p1`: dùng để kiểm tra diff có thể đảo lại trên bản bàn giao. |
| Jazzy thực tế, Gazebo Harmonic, Raspberry Pi 5, điện/encoder/IMU thật | **CHƯA KIỂM TRA**. |

Log kết quả gọn nằm ở `migration/evidence/`. Lần chạy trong sandbox có 11 test
qua, 1 test joystick lỗi kèm `Operation not permitted` khi tạo socket DDS.
Đã chạy lại ngoài sandbox, cả 12 qua; không sửa source hay test để bỏ qua lỗi.
Colcon cũng bị treo chờ subprocess trong sandbox; lần build ngoài sandbox
hoàn tất 9 package trong khoảng 8 giây với các artifact đã có từ các bước trước.
Một số package được build qua nhiều lần do giới hạn môi trường, không phải
phép đo thời gian build mới trên Pi.

## Lặp lại trên Pi/Jazzy

Sau khi cài dependency và build theo README, từ workspace mới:

```bash
source /opt/ros/jazzy/setup.bash
./tools/validate_jazzy.sh
```

Script có kiểm tra distro, đọc URDF, chạy test serial bằng pseudo-terminal,
build/run probe C++ và `real_robot --show-args`. Không khởi động driver trên
`/dev/ttyUSB0` thật. Cần `python3-pytest` và dependency đã được cài. Probe có
thể phát cảnh báo deprecated vì cố ý kiểm tra API cũ mà bản chuyển giữ lại.

Sau khi script qua, vẫn phải nghiệm thu trên phần cứng theo README: controller
active, clock thật, đúng firmware/baud/cổng/chiều quay, encoder/IMU/TF. Có thể
ghi kết quả Pi tại đây cùng phiên bản gói (`dpkg-query`) để người dùng khác tái
hiện. Kết quả Humble không được dùng thay cho xác nhận Jazzy/Pi.

## Sửa quyền thực thi sau báo cáo lỗi trên Pi

Lần launch trên Pi phát hiện `Mpu6050.py` thiếu quyền `x`. Kiểm tra trước chỉ build và `--show-args` chưa phát hiện vì chưa tra executable của node. Đã sửa mode của MPU6050 và hai script localization có cùng lỗi, thêm kiểm tra `install(PROGRAMS)`/symlink executable và manifest quyền thực thi. Không thay nội dung các node. Kiểm tra discovery của cả 7 chương trình qua symlink đã qua; chưa chạy IMU thật trên Pi.
