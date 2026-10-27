# Thử motor qua serial bằng node ROS thường

Package này chạy độc lập với `ros2_control`, không dùng lifecycle node, không nạp
`BumperbotInterface` và không spawn controller. Dùng được với ROS 2 Humble/Jazzy.
Chỉ build package này, không cần build lại `bumperbot_firmware`.

## Giao thức và phạm vi

Giả định vi điều khiển đang nhận giao thức của driver C++ đã cung cấp:

```text
rp01.00,ln02.50,
```

`r` = bánh phải, `l` = bánh trái, `p` = dương, `n` = âm. Giá trị là vận tốc bánh
theo rad/s, luôn có hai chữ số trước và hai chữ số sau dấu chấm. Baud mặc định
115200. Không tự thêm newline vào lệnh. Lệnh dừng là `rp00.00,lp00.00,`.
Firmware nhận PWM hoặc UDP sẽ không dùng trực tiếp được node này.
Chưa thay đổi hoặc nạp lại firmware vi điều khiển.

Node nhận `geometry_msgs/msg/TwistStamped` trên `/bumperbot_controller/cmd_vel`.
Topic này giữ tên cũ để dễ chuyển sang thử serial, nhưng không có controller nào
trong launch này. Khi chạy nhiều máy, timestamp yêu cầu đồng hồ đồng bộ; thử đầu
tiên nên publish ngay trên Pi. Timestamp bằng 0, quá cũ hoặc ở tương lai quá
0,1 giây đều bị từ chối và đưa vận tốc về 0.

Mặc định: bán kính 0,034 m; khoảng cách hai bánh 0,2565 m; giới hạn 0,10 m/s,
0,50 rad/s; giới hạn bánh 5 rad/s. Chuỗi lệnh gửi ở 20 Hz. Hai bánh được giảm
cùng tỷ lệ nếu vượt giới hạn vận tốc bánh, để giữ tỷ lệ rẽ.

Đây là node **thử serial/motor**. Phản hồi serial chỉ được xuất dạng chuỗi thô
(có thể là các mảnh dòng) trên `/serial_motor_node/serial_rx`; chưa tính odometry,
chưa xuất TF hoặc `/joint_states`. Lệnh đã ghi ra cổng nằm trên
`/serial_motor_node/serial_tx`. Ghi thành công không phải xác nhận motor đã quay.

## Chép sang Pi và build

Nếu triển khai trên Pi, chép cả thư mục `bumperbot_serial` này vào
`~/bumperbot_ws/src/bumperbot_serial/` trên Pi. Không chép thư mục `build`/`install`
từ máy tính sang Pi: cần build lại trên Pi.

Nếu dùng gói ZIP đi kèm, lưu vào `~/Downloads/bumperbot_serial.zip` trên Pi và
giải nén (ZIP đã chứa thư mục gốc `bumperbot_serial`):

```bash
unzip ~/Downloads/bumperbot_serial.zip -d ~/bumperbot_ws/src
```

Trên Pi dùng Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install python3-serial ros-jazzy-joy ros-jazzy-teleop-twist-joy
cd ~/bumperbot_ws
colcon build --packages-select bumperbot_serial --symlink-install
source install/setup.bash
```

Trên máy tính Humble, thay `jazzy` bằng `humble` trong lệnh source và tên package apt.
Chỉ cần cài `joy`/`teleop_twist_joy` nếu muốn chạy joystick.

## Thử với lệnh ROS

Dừng launch cũ, lệnh publish cũ và các chương trình khác dùng cùng cổng serial.
Kê robot để bánh không chạm đất khi kiểm tra chiều quay lần đầu. Cổng serial
được mở độc quyền; nếu không mở được, node in lỗi cụ thể và kết thúc launch.

Terminal 1 trên Pi:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bumperbot_ws/install/setup.bash
ros2 launch bumperbot_serial serial_motor_test.launch.py \
  serial_port:=/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0
```

Đợi thông báo `Serial ready`. Terminal 2 trên Pi:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bumperbot_ws/install/setup.bash
ros2 topic pub -r 20 /bumperbot_controller/cmd_vel \
  geometry_msgs/msg/TwistStamped \
  '{header: auto, twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'
```

Nhấn Ctrl+C để dừng publish lệnh 0, rồi thử chạy thẳng chậm:

```bash
ros2 topic pub -r 20 /bumperbot_controller/cmd_vel \
  geometry_msgs/msg/TwistStamped \
  '{header: auto, twist: {linear: {x: 0.05}, angular: {z: 0.0}}}'
```

Với kích thước mặc định, lệnh 0,05 m/s tạo chuỗi `rp01.47,lp01.47,`.
Nhấn Ctrl+C ở terminal publish: node gửi 0 sau khi lệnh hết hạn 0,25 giây,
cộng tối đa một chu kỳ gửi (0,05 giây). Nhấn Ctrl+C ở terminal launch:
node cố gửi lệnh 0 rồi đóng cổng, không chờ `flush()` vô thời hạn.

Xem dữ liệu (terminal khác):

```bash
ros2 topic echo /serial_motor_node/serial_tx
ros2 topic echo /serial_motor_node/serial_rx
```

Nếu bánh quay ngược với ý nghĩa vận tốc dương, dừng launch rồi chỉnh riêng bánh:

```bash
ros2 launch bumperbot_serial serial_motor_test.launch.py \
  serial_port:=/dev/ttyUSB0 left_direction:=-1 right_direction:=1
```

## Joystick

Dừng publish thử và launch serial cũ trước, rồi chạy:

```bash
ros2 launch bumperbot_serial serial_motor_test.launch.py \
  serial_port:=/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 \
  start_joystick:=true
```

Giữ nút index 5; trục 1 tiến/lùi, trục 3 quay. Nhả nút gửi vận tốc 0.
Mapping nằm trong `config/joystick.yaml`, giống các index của cấu hình cũ.
Joystick tự lặp 20 Hz và gửi `TwistStamped`. Có thể cần đổi index theo tay cầm.

Các tùy chọn khác xem bằng:

```bash
ros2 launch bumperbot_serial serial_motor_test.launch.py --show-args
```

## Khi gặp lỗi

- `Permission denied`: kiểm tra quyền thiết bị và nhóm `dialout` trên Pi.
- `Could not exclusively lock port`: kiểm tra `fuser -v <cổng>`, dừng driver/Serial
  Monitor đang dùng cổng. Node khác không được chạy song song với driver này.
- Không có `serial_rx`: có thể firmware không gửi phản hồi; chưa đủ để kết luận
  lỗi kết nối. Kiểm tra baud và đúng firmware.
- Có chuỗi TX nhưng motor không quay: kiểm tra giao thức thực tế, nguồn motor,
  dây, driver và firmware. Node không chứng minh phần điện đang hoạt động.
- Rút USB hoặc lỗi I/O: node ghi lỗi và kết thúc, không tự nối lại để chạy tiếp.

Watchdog ở đây nằm trên máy chạy ROS. Nếu Pi mất nguồn, node bị `kill -9` hoặc
USB ngắt, lệnh dừng có thể không tới vi điều khiển. Firmware cần watchdog riêng
để tự dừng motor khi không nhận lệnh; package này chưa sửa firmware đó.

## Kiểm thử bằng serial giả lập

Sau khi build và source workspace:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest src/bumperbot_serial/test -q
```

Test runtime tạo pseudo-terminal thay cho USB, dùng ROS domain riêng và không
đụng thiết bị thật. Kiểm tra luồng ROS -> serial, giới hạn tốc độ, timestamp,
watchdog, phản hồi RX, lệnh dừng khi SIGINT, khóa độc quyền cổng, nút giữ joystick
và kết thúc khi ngắt serial (kể cả khi đang bật joystick).
Đã thiết kế để chạy trên Linux. Cần `python3-pytest` để chạy test.

Đã build và chạy thành công 12 kiểm thử trên ROS 2 Humble tại máy tính.
Chưa kiểm thử trên Jazzy/Pi hoặc motor thật; cần xác nhận vi điều khiển đang nạp
firmware đúng giao thức serial nêu ở đầu tài liệu.
