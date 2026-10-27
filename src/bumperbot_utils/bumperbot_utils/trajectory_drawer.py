import rclpy 
from rclpy.node import Node
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

class TrajectoryDrawer(Node):
    def __init__(self):
        super().__init__("trajectory_drawer")

        self.path_ = Path()

        self.odom_sub_ = self.create_subscription(Odometry, "bumperbot_controller/odom", self.OdomCallback, 10)
        self.path_pub_ = self.create_publisher(Path, "bumperbot_controller/path", 10)

    def OdomCallback(self, msg):
        pose_now = PoseStamped()
        pose_now.header.frame_id = msg.header.frame_id
        pose_now.header.stamp = msg.header.stamp
        pose_now.pose.position.x = msg.pose.pose.position.x
        pose_now.pose.position.y = msg.pose.pose.position.y
        pose_now.pose.position.z = msg.pose.pose.position.z
        pose_now.pose.orientation.x = msg.pose.pose.orientation.x
        pose_now.pose.orientation.y = msg.pose.pose.orientation.y
        pose_now.pose.orientation.z = msg.pose.pose.orientation.z
        pose_now.pose.orientation.w = msg.pose.pose.orientation.w
        
        self.path_.header.frame_id = msg.header.frame_id 
        self.path_.header.stamp = msg.header.stamp

        self.path_.poses.append(pose_now)

        self.path_pub_.publish(self.path_)

def main():
    rclpy.init()
    trajectory_drawer = TrajectoryDrawer()
    rclpy.spin(trajectory_drawer)
    trajectory_drawer.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
