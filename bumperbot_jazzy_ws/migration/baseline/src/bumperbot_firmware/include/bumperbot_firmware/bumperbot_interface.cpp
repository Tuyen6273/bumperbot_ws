#include "bumperbot_firmware/bumperbot_interface.hpp"
#include <hardware_interface/types/hardware_interface_type_values.hpp>

namespace bumperbot_firmware
{
BumperbotInterface::BumperbotInterface()
{

}

BumperbotInterface::~BumperbotInterface() //Destructor huy object giao tiếp với arduino
{
    if(arduino_.IsOpen())
    {
        try
        {
            arduino_.Close();
        }
        catch(...)
        {
            RCLCPP_FATAL_STREAM(rclcpp::get_logger("BumperbotInterface"), "Something went wrong while closing the connection with port " << port_);
        }
    }
}

CallbackReturn BumperbotInterface::on_init(const hardware_interface::HardwareInfo & hardware_info)
{
    CallbackReturn result = hardware_interface::SystemInterface::on_init(hardware_info);
    if(result != CallbackReturn::SUCCESS)
    {
        return result;
    }
    try
    {
        serial_ports_ = {
            info_.hardware_parameters.at("port"),
            info_.hardware_parameters.at("fallback_port")
        };
    }
    catch(const std::out_of_range &e) // Nếu không tìm thấy tham số "port" hoặc "fallback_port" 
    // trong hardware_info, sẽ ném ra ngoại lệ std::out_of_range
    {
        RCLCPP_FATAL(rclcpp::get_logger("BumperbotInterface"), "No serial port provided! Aborting");
        return CallbackReturn::FAILURE;
    }
    velocity_commands_.reserve(info_.joints.size());
    position_states_.reserve(info_.joints.size());
    velocity_states_.reserve(info_.joints.size());
    Last_run_ = rclcpp::Clock().now();

    return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> BumperbotInterface::export_state_interfaces()
// hàm tên là export_state_interfaces, trả về một vector chứa các đối tượng StateInterface.
{
    std::vector<hardware_interface::StateInterface> state_interfaces;
    // Tạo một vector rỗng để lưu trữ các đối tượng StateInterface.
    for(size_t i = 0; i < info_.joints.size(); i++)
    // Lặp qua tất cả các khớp (joints) được định nghĩa trong thông tin phần cứng (hardware_info).
    //i = 0 → wheel_right_base_joint
    //i = 1 → wheel_left_base_joint
    {
        state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.joints[i].name, hardware_interface::HW_IF_POSITION, &position_states_[i]));
        state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &velocity_states_[i]));
        // Tạo hai đối tượng StateInterface cho mỗi khớp:
        // info_.joints[i].name: Tên của khớp hiện tại.
        // hardware_interface::HW_IF_POSITION: Giao diện trạng thái cho vị trí.
        // &position_states_[i]: Con trỏ đến giá trị vị trí của khớp hiện tại.
        // hardware_interface::HW_IF_VELOCITY: Giao diện trạng thái cho vận tốc.
        // &velocity_states_[i]: Con trỏ đến giá trị vận tốc của khớp hiện tại.
        // Các đối tượng StateInterface này được thêm vào vector state_interfaces bằng cách sử dụng phương thức 
        // emplace_back, giúp tạo đối tượng trực tiếp trong vector
    }

    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> BumperbotInterface::export_command_interfaces()
{
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    // Tạo một vector rỗng để lưu trữ các đối tượng CommandInterface.
    for(size_t i = 0; i < info_.joints.size(); i++)
    {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(info_.joints[i].name,
                                        hardware_interface::HW_IF_VELOCITY, &velocity_commands_[i]));
        // Tạo một đối tượng CommandInterface cho mỗi khớp:
        // Mỗi CommandInterface chứa: tên joint + loại lệnh + địa chỉ của giá trị lệnh (velocity_commands_[i]) để điều khiển vận tốc của khớp.
        // Các đối tượng CommandInterface này được thêm vào vector command_interfaces bằng cách sử dụng phương thức emplace_back, giúp tạo đối tượng trực tiếp trong vector.
    }
    return command_interfaces;
}
CallbackReturn BumperbotInterface::on_activate(const rclcpp_lifecycle::State & previous_state)
{
    RCLCPP_INFO(rclcpp::get_logger("BumperbotInterface"), "Starting robot hardware...");
    velocity_commands_ = {0.0, 0.0};
    position_states_ = {0.0, 0.0};
    velocity_states_ = {0.0, 0.0};

    for (const auto &candidate : serial_ports_)
{
    try
    {
        arduino_.Open(candidate);
        arduino_.SetBaudRate(LibSerial::BaudRate::BAUD_115200);

        port_ = candidate;

        RCLCPP_INFO_STREAM(
            rclcpp::get_logger("BumperbotInterface"),
            "Connected to " << port_);

        return CallbackReturn::SUCCESS;
    }
    catch (...)
    {
        RCLCPP_WARN_STREAM(
            rclcpp::get_logger("BumperbotInterface"),
            "Cannot connect to " << candidate
                                << "; trying the next port");

        // Dọn kết nối nếu Open thành công nhưng SetBaudRate lỗi
        try
        {
            if (arduino_.IsOpen())
            {
                arduino_.Close();
            }
        }
        catch (...)
        {
            return CallbackReturn::FAILURE;
        }
    }
}

RCLCPP_FATAL(
    rclcpp::get_logger("BumperbotInterface"),
    "Cannot connect to any configured port");

return CallbackReturn::FAILURE;
}
CallbackReturn BumperbotInterface::on_deactivate(const rclcpp_lifecycle::State & previous_state)
{
    RCLCPP_INFO(rclcpp::get_logger("BumperbotInterface"), "Stopping robot hardware...");
    if(arduino_.IsOpen())
    {
        try
        {
            arduino_.Close();
        }
        catch(...)
        {
            RCLCPP_FATAL_STREAM(rclcpp::get_logger("BumperbotInterface"), "Something went wrong while closing the port" << port_);
            return CallbackReturn::FAILURE;
        }
        
    }
}
hardware_interface::return_type BumperbotInterface::read(const rclcpp::Time & time, const rclcpp::Duration & period)
{
    if(arduino_.IsDataAvailable())
    {
        auto dt = (rclcpp::Clock().now() - Last_run_).seconds();
        std::string message;
        arduino_.ReadLine(message);
        std::stringstream ss(message);
        std::string res;
        int multiplier = 1;
        while(std::getline(ss, res, ','))
        {
            multiplier = res.at(1) == 'p' ? 1:-1;
            if(res.at(0) == 'r')
            {
                velocity_states_.at(0) = multiplier*std::stod(res.substr(2, res.size()));
                position_states_.at(0) += velocity_states_.at(0)*dt;
            }
            else if(res.at(0) == 'l')
            {
                velocity_states_.at(1) = multiplier*std::stod(res.substr(2, res.size()));
                position_states_.at(1) += velocity_states_.at(1)*dt;
            }
        }
        Last_run_ = rclcpp::Clock().now();
    }
    return hardware_interface::return_type::OK;
}

hardware_interface::return_type BumperbotInterface::write(const rclcpp::Time & time, const rclcpp::Duration & period)
{
    std::stringstream message_stream;
    char right_wheel_sign = velocity_commands_.at(0) >= 0 ? 'p' : 'n';
    char left_wheel_sign = velocity_commands_.at(1) >= 0 ? 'p' : 'n';

    std::string compensate_zeros_right ="";
    std::string compensate_zeros_left ="";

    if(std::abs(velocity_commands_.at(0)) < 10.0)
    {
        compensate_zeros_right = "0";
    }
    else
    {
        compensate_zeros_right = "";
    }

    if(std::abs(velocity_commands_.at(1)) < 10.0)
    {
        compensate_zeros_left = "0";
    }
    else
    {
        compensate_zeros_left = "";
    }

    message_stream << std::fixed << std::setprecision(2) << "r" << right_wheel_sign << compensate_zeros_right << std::abs(velocity_commands_.at(0)) <<
    ",l" << left_wheel_sign << compensate_zeros_left << std::abs(velocity_commands_.at(1)) << ",";

    try
    {
        arduino_.Write(message_stream.str());
    }
    catch(...)
    {
        RCLCPP_ERROR_STREAM(rclcpp::get_logger("BumperbotInterface"), "Something went wrong while sending the message " <<
            message_stream.str() << "to the port" << port_);
        return hardware_interface::return_type::ERROR;
    }
    return hardware_interface::return_type::OK;
}
    
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(bumperbot_firmware::BumperbotInterface, hardware_interface::SystemInterface);
