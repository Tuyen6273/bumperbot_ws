import rclpy
from rclpy.node import Node
from bumperbot_msgs.srv import AddTwoInts
import time

class SimpleServiceServer(Node):
    def __init__(self):
        super().__init__("simple_service_server")

        self.frequency = 0.5

        self.service_ = self.create_service(AddTwoInts,"add_two_ints", self.ServiceCallback)

        self.get_logger().info("Service add_two_ints is ready")

        self.timer = self.create_timer(self.frequency, self.timer_callback)

    def ServiceCallback(self, request, response):
        self.get_logger().info("New Request Service a: %d, b: %d " %(request.a, request.b))
        response.sum = request.a + request.b
        self.get_logger().info('Starting calculate .......')
        time.sleep(10.0)
        self.get_logger().info("Returning sum: %d " %response.sum)

        return response

    def timer_callback(self):
        self.get_logger().info('Program is running......')

def main():
    rclpy.init()
    simple_service_server = SimpleServiceServer()
    rclpy.spin(simple_service_server)
    simple_service_server.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
