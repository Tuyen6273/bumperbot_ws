import rclpy
from rclpy.node import Node
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from tf2_ros import TransformBroadcaster, TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from geometry_msgs.msg import TransformStamped
from bumperbot_msgs.srv import GetTransform
from tf_transformations import quaternion_from_euler, quaternion_multiply, quaternion_inverse

class SimpleTfKinematics(Node):
    def __init__(self):
        super().__init__("simple_tf_kinematics")

        self.static_tf_broadcaster_ = StaticTransformBroadcaster(self)
        self.dynamic_tf_broadcaster_ = TransformBroadcaster(self)

        self.static_transform_stamped_ = TransformStamped()
        self.dynamic_transform_stamped_ = TransformStamped()

        # set variable movement
        self.x_increment_ = 0.005
        self.last_x_ = 0.0
        self.y_increment_ = 0.003
        self.last_y_ = 0.0
        self.z_increment_ = 0.01
        self.last_z_ = 0.0
        self.rotations_counter_ = 0
        self.last_orientation_ = quaternion_from_euler(0, 0, 0)
        # kết quả thu được là một mảng có 4 index, mỗi index là một giá trị của quaternion (x, y, z, w)
        self.orientation_increment_ = quaternion_from_euler(0,0, 0.05) 



        self.tf_buffer = Buffer() # tạo một bộ nhớ lưu các transform, lưu thông tin quan hệ giữa các frame theo thời gian
        self.tf_listener = TransformListener(self.tf_buffer, self)
        #Tạo một đối tượng lắng nghe dữ liệu TF từ các topic /tf và /tf_static, rồi đưa dữ liệu nhận được vào tf_buffer.
        

        self.static_transform_stamped_.header.stamp = self.get_clock().now().to_msg()

        self.static_transform_stamped_.header.frame_id = "bumperbot_base"
        self.static_transform_stamped_.child_frame_id = "bumperbot_top"
        self.static_transform_stamped_.transform.translation.x = 0.0 
        self.static_transform_stamped_.transform.translation.y = 0.0 
        self.static_transform_stamped_.transform.translation.z = 0.3
        self.static_transform_stamped_.transform.rotation.x = 0.0 
        self.static_transform_stamped_.transform.rotation.y = 0.0 
        self.static_transform_stamped_.transform.rotation.z = 0.0 
        self.static_transform_stamped_.transform.rotation.w = 1.0

        self.static_tf_broadcaster_.sendTransform(self.static_transform_stamped_)

        self.get_logger().info("Publishing static transform between %s and %s" 
                               %(self.static_transform_stamped_.header.frame_id, self.static_transform_stamped_.child_frame_id))
        self.timer = self.create_timer(0.1, self.TimerCallback)

        self.get_transform_srv_ = self.create_service(GetTransform, 'get_transform', self.GetTransformCallback)

    def TimerCallback(self):
        self.dynamic_transform_stamped_.header.stamp = self.get_clock().now().to_msg()
        self.dynamic_transform_stamped_.header.frame_id = "odom"
        self.dynamic_transform_stamped_.child_frame_id ="bumperbot_base"

        # set dynamic transformation 
        self.dynamic_transform_stamped_.transform.translation.x = self.last_x_ + self.x_increment_
        self.dynamic_transform_stamped_.transform.translation.y = self.last_y_ + self.y_increment_
        self.dynamic_transform_stamped_.transform.translation.z = self.last_z_ + self.z_increment_
        q = quaternion_multiply(self.last_orientation_, self.orientation_increment_)
        self.dynamic_transform_stamped_.transform.rotation.x = q[0]
        self.dynamic_transform_stamped_.transform.rotation.y = q[1]
        self.dynamic_transform_stamped_.transform.rotation.z = q[2]
        self.dynamic_transform_stamped_.transform.rotation.w = q[3]

        self.dynamic_tf_broadcaster_.sendTransform(self.dynamic_transform_stamped_)

        # update the position of the robot
        self.last_x_ = self.dynamic_transform_stamped_.transform.translation.x
        self.last_y_ = self.dynamic_transform_stamped_.transform.translation.y
        self.last_z_ = self.dynamic_transform_stamped_.transform.translation.z

        self.rotations_counter_ += 1
        self.last_orientation_ = q

        if self.rotations_counter_ >= 100:
            self.get_logger().info("Switching the orientation of the robot")
            self.orientation_increment_ = quaternion_inverse(self.orientation_increment_)
            self.rotations_counter_ = 0

    def GetTransformCallback(self, req, res):
        self.get_logger().info("Request transform between %s and %s" %(req.frame_id, req.child_frame_id))
        requested_transform = TransformStamped()
        # thực hiện tra cứu transform giữa hai frame được yêu cầu, nếu không tìm thấy sẽ ném ra ngoại lệ TransformException
        try:
            requested_transform = self.tf_buffer.lookup_transform(req.frame_id, req.child_frame_id, rclpy.time.Time())
        except TransformException as e:
            self.get_logger().error("An error occured while transforming %s and %s" % (req.frame_id, req.child_frame_id))
            res.success = False
            return res
        res.transform = requested_transform
        res.success = True
        return res

def main():
    rclpy.init()
    simple_tf_kinematics = SimpleTfKinematics()
    rclpy.spin(simple_tf_kinematics)
    simple_tf_kinematics.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
