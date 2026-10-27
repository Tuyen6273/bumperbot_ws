import rclpy 
from rclpy.node import Node
from bumperbot_msgs.srv import AddTwoInts
import sys

class SimpleServiceClient(Node):
    def __init__(self, a, b):
        super().__init__("simple_service_client")
        # Khoi tao mot client moi
        self.frequency = 0.5
        self.client_ = self.create_client(AddTwoInts, 'add_two_ints')

        while not self.client_.wait_for_service(timeout_sec= 1.0):
            self.get_logger().info("Service not available, waiting again....")

        self.req_ = AddTwoInts.Request() # Tao mot doi tuong request moi theo cau truc viet trong file srv
        self.req_.a = a
        self.req_.b = b

        self.future_ = self.client_.call_async(self.req_)
        self.future_.add_done_callback(self.responseCallback)
        self.timer = self.create_timer(self.frequency, self.timer_callback)

    def responseCallback(self, future):
        self.get_logger().info("Service response: %d" %future.result().sum)

    def timer_callback(self):
            self.get_logger().info('Program is running......')

def main():
    rclpy.init()
    if len(sys.argv) != 3:
        print("Wrong number of arguments! Usage: simple_service_client A B")
        return -1
    simple_service_client = SimpleServiceClient(int(sys.argv[1]), int(sys.argv[2]))
    rclpy.spin(simple_service_client)
    simple_service_client.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()