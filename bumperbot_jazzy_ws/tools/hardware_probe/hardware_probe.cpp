// Integration check against a pseudo-terminal. Never opens a real motor device.
#include <hardware_interface/system_interface.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/rclcpp.hpp>
#include <pty.h>
#include <poll.h>
#include <unistd.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

void require(bool ok, const std::string & what)
{
  if (!ok) throw std::runtime_error(what);
}

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  int master = -1, slave = -1;
  try {
    char name[128];
    require(openpty(&master, &slave, name, nullptr, nullptr) == 0, "openpty");
    pluginlib::ClassLoader<hardware_interface::SystemInterface> loader(
      "hardware_interface", "hardware_interface::SystemInterface");
    auto driver = loader.createSharedInstance("bumperbot_firmware/BumperbotInterface");
    hardware_interface::HardwareInfo info;
    info.name = "BumperbotSystem";
    info.type = "system";
    info.hardware_parameters["port"] = "/nonexistent/bumperbot-test-port";
    info.hardware_parameters["fallback_port"] = name;
    for (const auto & joint_name : {"wheel_right_base_joint", "wheel_left_base_joint"}) {
      hardware_interface::ComponentInfo joint;
      joint.name = joint_name;
      joint.type = "joint";
      hardware_interface::InterfaceInfo position, velocity;
      position.name = "position";
      velocity.name = "velocity";
      joint.state_interfaces = {position, velocity};
      joint.command_interfaces = {velocity};
      info.joints.push_back(joint);
    }
    using CallbackReturn = hardware_interface::CallbackReturn;
    require(driver->on_init(info) == CallbackReturn::SUCCESS, "on_init");
    auto states = driver->export_state_interfaces();
    auto commands = driver->export_command_interfaces();
    require(states.size() == 4 && commands.size() == 2, "export before activation");
    rclcpp_lifecycle::State previous;
    require(driver->on_activate(previous) == CallbackReturn::SUCCESS, "fallback/activate");
    commands[0].set_value(1.0);
    commands[1].set_value(-2.5);
    auto now = rclcpp::Clock().now();
    auto period = rclcpp::Duration::from_seconds(0.01);
    require(driver->write(now, period) == hardware_interface::return_type::OK, "write");
    pollfd fd{master, POLLIN, 0};
    require(poll(&fd, 1, 1000) > 0, "serial TX timeout");
    char buffer[128];
    auto count = ::read(master, buffer, sizeof(buffer));
    require(count > 0 && std::string(buffer, count) == "rp01.00,ln02.50,", "wire protocol changed");
    const std::string response = "rp01.25,ln02.50,\r\n";
    require(::write(master, response.data(), response.size()) ==
      static_cast<ssize_t>(response.size()), "serial RX injection");
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    require(driver->read(now, period) == hardware_interface::return_type::OK, "read");
    require(std::abs(states[1].get_value() - 1.25) < 1e-9, "right feedback");
    require(std::abs(states[3].get_value() + 2.5) < 1e-9, "left feedback");
    require(states[0].get_value() > 0 && states[2].get_value() < 0, "position integration");
    require(driver->on_deactivate(previous) == CallbackReturn::SUCCESS, "deactivate");
    std::cout << "PASS: plugin load, allocation, fallback, TX, encoder RX, position, lifecycle\n";
  } catch (const std::exception & e) {
    std::cerr << "FAIL: " << e.what() << '\n';
    if (master >= 0) close(master);
    if (slave >= 0) close(slave);
    rclcpp::shutdown();
    return 1;
  }
  close(master);
  close(slave);
  rclcpp::shutdown();
  return 0;
}
