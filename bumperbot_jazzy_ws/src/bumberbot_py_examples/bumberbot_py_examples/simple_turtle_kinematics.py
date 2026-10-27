import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
import math

class SimpleTurtleKinematics(Node):

    def __init__(self):
        super().__init__("simple_turtle_kinematics")

        self.turtle1_pose = Pose()
        self.turtle2_pose = Pose()

        self.turtle1_pose_subcriber = self.create_subscription(Pose, "/turtle1/pose", self.turtle1_pose_callback, 10)
        self.turtle2_pose_subcriber = self.create_subscription(Pose, "/turtle2/pose", self.turtle2_pose_callback, 10)

    def turtle1_pose_callback(self, msg):
        self.turtle1_pose = msg
        self.calculate_translation()

    def turtle2_pose_callback(self, msg):
        self.turtle2_pose = msg
        self.calculate_translation()

    def calculate_translation(self):
        if self.turtle1_pose is None or self.turtle2_pose is None:
            return

        tx = self.turtle2_pose.x  - self.turtle1_pose.x
        ty = self.turtle2_pose.y  - self.turtle1_pose.y

        theta_rad = self.turtle2_pose.theta - self.turtle1_pose.theta
        theta_deg = 180 * theta_rad/ 3.14

        self.get_logger().info(
            """Translation Vector turtule1 -> turtle2 \n
                    Tx: %f \n
                    Ty: %f \n
                    Rotation Matrix turtle1 -> turtle2\n
                    theta(rad): %f\n
                    theta(deg): %f \n 
                    |R11       R12|   :   |%f     %f|\n
                    |R21       R22|   :   |%f     %f|\n""" %(tx, ty, theta_rad, theta_deg, math.cos(theta_rad), -math.sin(theta_rad),
                                                             math.sin(theta_rad), math.cos(theta_rad))
        )

def main():
    rclpy.init()
    simple_turtle_kinematics = SimpleTurtleKinematics()
    rclpy.spin(simple_turtle_kinematics)
    simple_turtle_kinematics.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()


########################################################
# Cach de chay file turtle truoc khi khoi chay node nay 
# Mo con turtle dau tien : ros2 run turtlesim turtlesim_node
# Spawn vao con turtle thu 2: '
#  ros2 service call /spawn turtlesim/srv/Spawn \
# "{x: 1.0, y: 4.0, theta: 0.0, name: 'turtle2'}"


