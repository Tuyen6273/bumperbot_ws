#ifndef BUMPERBOT_INTERFACE_HPP
#define BUMPERBOT_INTERFACE_HPP
#include <rclcpp/rclcpp.hpp> // cung cấp các chức năng của ROS 2 C++ client library
#include <hardware_interface/system_interface.hpp> // Lớp cha tạo sự kết thùa chức năng của ros2 control
#include <rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <vector> // thư viện của cpp cung cấp dynamic array
#include <libserial/SerialPort.h>
#include <string>

namespace bumperbot_firmware // tránh trùng tên class với các package khác
{
using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;
// Là kiểu dữ liệu trả về của các hàm life cycle trong ROS 2. 
// Nó được sử dụng để chỉ định trạng thái của một nút (node) trong vòng đời của nó, ví dụ như thành công, thất bại hoặc lỗi. 

class BumperbotInterface : public hardware_interface::SystemInterface // kế thừa
{
public:
    BumperbotInterface();
    virtual ~BumperbotInterface();

    virtual CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override; // được gọi khi hardware chuyển từ inactive sang active
    virtual CallbackReturn on_deactivate(const rclcpp_lifecycle::State & previous_state) override; // được gọi khi hardware chuyển từ active sang inactive
    virtual CallbackReturn on_init(const hardware_interface::HardwareInfo & hardware_info) override; // được gọi khi hardware được khởi tạo, nhận thông tin từ URDF

    virtual std::vector<hardware_interface::StateInterface> export_state_interfaces() override; // xuất các giao diện trạng thái

    virtual std::vector<hardware_interface::CommandInterface> export_command_interfaces() override; // xuất các giao diện lệnh

    virtual hardware_interface::return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override; // đọc sữ liệu từ phần cứng và cập nhật các giao diện trạng thái

    virtual hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override; // ghi dữ liệu lệnh từ các giao diện lệnh đến phần cứng
    // time là thời gian bắt đầu của vòng lặp điều khiển hiện tại, period là thời gian đo được của vòng lặp điều khiển trước đó.
    // duration là một lớp trong ROS 2 C++ client library (rclcpp) đại diện cho khoảng thời gian, thường được sử dụng để biểu diễn thời gian trôi qua hoặc khoảng thời gian giữa các sự kiện. Nó có thể được sử dụng để tính toán thời gian trễ, đo lường hiệu suất, hoặc điều khiển vòng lặp điều khiển trong các ứng dụng robot.
private:
    LibSerial::SerialPort arduino_;
    // object giao tiếp với arduino

    std::string port_;
    std::vector<std::string> serial_ports_;
    std::vector<double> velocity_commands_;
    std::vector<double> velocity_states_;
    std::vector<double> position_states_;

    rclcpp::Time Last_run_;
};
}



#endif