import rclpy
from rclpy.node import Node
import pygame
from geometry_msgs.msg import TwistStamped


class JoystickPublisher(Node):
    def __init__(self):
        super().__init__("joystick_publisher")

        # Khai bao cac Parameter
        self.declare_parameter("wheel_radius", 0.034)
        self.declare_parameter("wheel_separation", 0.2565)
        self.declare_parameter("deadzone_joystick", 0.2)
        self.declare_parameter("max_linear_speed", 0.8) # 0.8 m/s
        self.declare_parameter("max_angular_speed", 1.5) # 1.5 rad/s

        self.wheel_radius_ = self.get_parameter("wheel_radius").get_parameter_value().double_value
                # Ham get parameter duoc su dung de lay du lieu tu parameter
                # get_parameter('ten_parameter') trả về một đối tượng rclpy.parameter.Parameter, không phải giá trị trực tiếp.
                #get_parameter_value() lấy giá trị parameter dưới dạng ROS 2 ParameterValue, trong đó mỗi kiểu dữ liệu nằm ở một thuộc tính riêng.
                # .integer_value        # int
                # .double_value         # float
                # .string_value         # str
                # .bool_value           # bool
                # .integer_array_value  # list[int]
                # .double_array_value   # list[float]
                # .string_array_value   # list[str]
        
        self.wheel_separation_ = self.get_parameter("wheel_separation").get_parameter_value().double_value
        self.deadzone_joystick = self.get_parameter("deadzone_joystick").get_parameter_value().double_value
        self.max_linear_speed = self.get_parameter("max_linear_speed").get_parameter_value().double_value
        self.max_angular_speed = self.get_parameter("max_angular_speed").get_parameter_value().double_value
        
        # 1. Khoi dong pygame
        pygame.init()
        pygame.joystick.init()
        # 2. Kiem tra gamepad 
        if pygame.joystick.get_count() == 0:
            pygame.joystick.quit()
            pygame.quit()
            raise RuntimeError("Khong tim thay gamepad")

        self.gamepad = pygame.joystick.Joystick(0) # tao doi tuong tay cam

        self.get_logger().info(f"Da ket noi voi gamepad: {self.gamepad.get_name()}")

        # tao publisher publish cmd_vel
        self.cmd_vel_publisher = self.create_publisher(TwistStamped, '/bumperbot_controller/cmd_vel', 10)

        self.timer = self.create_timer(0.01, self.timer_callback)
        
    def apply_deadzone(self, value):
        if(abs(value) <= self.deadzone_joystick):
            return 0.0
        return value
    def timer_callback(self):
        pygame.event.get() # dung de xu ly cac su kien khi dung tay cam 

        axis_linear = self.apply_deadzone(self.gamepad.get_axis(1))
        axis_angular = self.apply_deadzone(self.gamepad.get_axis(3))
        bumper_right = self.gamepad.get_button(5)
        linear_x = -axis_linear*self.max_linear_speed
        angular_z = -axis_angular*self.max_angular_speed

        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        if bumper_right:
            msg.twist.linear.x = linear_x
            msg.twist.angular.z = angular_z

        else:
            msg.twist.linear.x = 0.0
            msg.twist.angular.z = 0.0
            
        self.cmd_vel_publisher.publish(msg)

    def destroy_node(self):
        self.get_logger().info("Dang tien hanh huy node joystick publisher!")

        if hasattr(self, 'timer'):
            self.timer.cancel()
        # kiem tra xem object hien hanh self co ton tai timer khong neu co thi huy di 

        pygame.joystick.quit()
        pygame.quit()

        return super().destroy_node()


def main():
    rclpy.init()
    joystick_publisher = JoystickPublisher()
    rclpy.spin(joystick_publisher)
    joystick_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()



    


       
