import rclpy
from rclpy.node import Node
from std_msgs.msg import String 
from std_msgs.msg import Int32

class SimplePublisher(Node):
    def __init__(self):
        super().__init__("simple_publisher") # khởi tạo tên cho node

        self.pub_ = self.create_publisher(String, "gui_du_lieu_string_qua_node", 10) # Khởi tạo pub với kiểu dữ liệu gửi
        #, tên topic và queue_size cho hàng đợi truyền thông tin
        self.pub_nhietdo = self.create_publisher(Int32, "gui_nhiet_do", 10)
        self.counter = 0
        self.frequency = 1.0
        self.nhiet_do = 32

        self.get_logger().info("Publishing at %d Hz" %self.frequency) # dùng để in ra một dòng info 
         # khởi tạo timer với 2 tham số là tấn só và một hàm call_back
        self.timer_ = self.timer_callback(1, self.timer_callback)

    def timer_callback(self):
        msgs = String() # khởi tạo dữ liệu truyền đi
        msgs_nhiet_do = Int32()
        msgs_nhiet_do.data = self.nhiet_do

        msgs.data = "Hello ROS2 - counter: %d" %self.counter # data truyền đi
        self.get_logger().info(msgs.data) # thông báo về dữ liệu được truyền đi
        self.get_logger().info('Nhiet do: %d' %msgs_nhiet_do.data) # thông báo về dữ liệu được truyền đi
        self.pub_.publish(msgs) # gửi msgs lên topic
        self.pub_nhietdo.publish(msgs_nhiet_do)
        self.counter +=1 

def main():
    rclpy.init() 
    simple_publisher = SimplePublisher()
    rclpy.spin(simple_publisher)
    simple_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()