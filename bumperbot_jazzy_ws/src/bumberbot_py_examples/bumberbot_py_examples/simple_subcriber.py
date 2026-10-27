import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Int32

class SimpleSubcriber(Node):
    def __init__(self):
        super().__init__("simple_subcriber")

        self.sub = self.create_subscription(String, "gui_du_lieu_string_qua_node", self.msgCallback, 10)
        self.sub1 = self.create_subscription(Int32, "gui_nhiet_do", self.msgCallback1, 10)

    def msgCallback(self, msg):
        self.get_logger().info("I heard: %s" %msg.data)
    def msgCallback1(self, msg):
        if msg.data >= 30: 
            self.get_logger().info("Nhiet do la %d (>=30): Bat den" %msg.data)
        else:
            self.get_logger().info("Nhiet do la %d (<30): Tat den" %msg.data)

def main():
    rclpy.init()
    simple_subcriber = SimpleSubcriber()
    rclpy.spin(simple_subcriber)
    simple_subcriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()





