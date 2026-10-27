#!/usr/bin/env python3
# CODE CU: giu lai de doi chieu, khong thuc thi.
# #!/usr/bin/env python3
# import random
# import time
# from math import sin, cos, atan2, sqrt, fabs, pi
#
# import rclpy
# from rclpy.node import Node
# from geometry_msgs.msg import Pose, PoseArray
# from nav_msgs.msg import Odometry
# from tf_transformations import quaternion_from_euler, euler_from_quaternion
# from tf_transformations import euler_from_quaternion
#
# def normalize(z):
#     return atan2(sin(z), cos(z))
#
# def angle_diff(a, b):
#     a = atan2(sin(a), cos(a)) # chuyen doi goc tu 0 den 2*pi thanh goc tu -pi den pi
#     b = atan2(sin(b), cos(b)) # chuyen doi goc tu 0 den 2*pi thanh goc tu -pi den pi
#     d1 = a - b # tru truc tiep 2 goc de tim ra goc chenh lech
#     d2 = 2 * pi - fabs(d1) # tinh goc chenh lech theo chieu nguoc lai cua 2 goc
#     if d1 > 0: # neu goc chenh lech d1 > 0 thi goc chenh lech d2 se co gia tri am
#         d2 *= -1.0
#     if fabs(d1) < fabs(d2): # so sanh 2 goc chenh lech d1 va d2 de lay ra goc chenh lech nho hon
#         return d1
#     else:
#         return d2
#
#
# class OdometryMotionModel(Node):
#     def __init__(self):
#
#         self.is_first_odom = True #bien nay xac nhan xem la da nhan duoc du lieu odom chua
#         self.last_odom_x = 0.0
#         self.last_odom_y = 0.0
#         self.last_odom_theta = 0.0
#
#         super().__init__('odometry_motion_model')
#         self.declare_parameter("alpha1", 0.1)
#         self.declare_parameter("alpha2", 0.1)
#         self.declare_parameter("alpha3", 0.1)
#         self.declare_parameter("alpha4", 0.1)
#         self.declare_parameter("nr_samples", 300) # soluong hat muon tao ra de the hien uoc luong vi tri cua robot
#
#         self.alpha1 = self.get_parameter("alpha1").get_parameter_value().double_value
#         self.alpha2 = self.get_parameter("alpha2").get_parameter_value().double_value
#         self.alpha3 = self.get_parameter("alpha3").get_parameter_value().double_value
#         self.alpha4 = self.get_parameter("alpha4").get_parameter_value().double_value   
#         self.nr_samples = self.get_parameter("nr_samples").get_parameter_value().integer_value
#
#         if self.nr_samples >= 0:
#             self.samples = PoseArray()
#             self.samples.poses = [Pose() for _ in range(self.nr_samples)]
#         else:
#             self.get_logger().fatal("Invalid number of samples requested: %d", self.nr_samples)
#             return
#
#         self.odom_sub_ = self.create_subscription(Odometry, "bumperbot_controller/odom", self.odomCallback, 10)
#         self.pose_array_pub_ = self.create_publisher(PoseArray, "odometry_motion_model/samples", 10)
#
#     def odomCallback(self, odom):
#         q = [odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, 
#              odom.pose.pose.orientation.z, odom.pose.pose.orientation.w]
#         roll, pitch, yaw = euler_from_quaternion(q)
#
#         if self.is_first_odom:
#             self.last_odom_x = odom.pose.pose.position.x
#             self.last_odom_y = odom.pose.pose.position.y
#             self.last_odom_theta = yaw
#
#             self.samples.header.frame_id = odom.header.frame_id
#             self.is_first_odom = False
#             return
#
#         odom_x_increment = odom.pose.pose.position.x - self.last_odom_x
#         odom_y_increment = odom.pose.pose.position.y - self.last_odom_y
#         odom_theta_increment = angle_diff(yaw, self.last_odom_theta)
#
#         if sqrt(pow(odom_x_increment, 2) + pow(odom_y_increment, 2)) < 0.01:
#             delta_rot1 = 0
#         else: 
#             delta_rot1 = angle_diff(atan2(odom_y_increment, odom_x_increment), yaw)
#         delta_translation = sqrt(pow(odom_x_increment, 2) + pow(odom_y_increment, 2))
#         delta_rot2 = angle_diff(odom_theta_increment, delta_rot1)
#
#         rot1_varience = self.alpha1 * delta_rot1 + self.alpha2 * delta_translation
#         translation_varience = self.alpha3 * delta_translation +self.alpha4 * (delta_rot1 + delta_rot2)
#         rot2_varience = self.alpha1 * delta_rot2 + self.alpha2 * delta_translation
#
#         random.seed(int(time.time()))
#         for sample in self.samples.poses:
#             rot1_noise = random.gauss(0.0, rot1_varience)
#             translation_noise = random.gauss(0.0, translation_varience)
#             rot2_noise = random.gauss(0.0, rot2_varience)
#
#             delta_rot1_draw = angle_diff(delta_rot1, rot1_noise)
#             delta_rot2_draw = angle_diff(delta_rot2, rot2_noise)
#             delta_translation_draw = delta_translation - translation_noise
#
#             sample_q = [sample.orientation.x, sample.orientation.y, sample.orientation.z, sample.orientation.w]
#             sample_roll, sample_pitch, sample_yaw = euler_from_quaternion(sample_q)
#             sample.position.x += delta_translation_draw * cos(sample_yaw + delta_rot1_draw)
#             sample.position.y += delta_translation_draw * sin(sample_yaw + delta_rot1_draw)
#             quaternion = quaternion_from_euler(0, 0, sample_yaw + delta_rot1_draw + delta_rot2_draw)
#             sample.orientation.x = quaternion[0]
#             sample.orientation.y = quaternion[1]
#             sample.orientation.z = quaternion[2]
#             sample.orientation.w = quaternion[3]
#         self.last_odom_x = odom.pose.pose.position.x
#         self.last_odom_y = odom.pose.pose.position.y
#         self.last_odom_theta = yaw
#         self.pose_array_pub_.publish(self.samples)
#
# def main():
#     rclpy.init()
#     odometry_motion_model = OdometryMotionModel()
#     rclpy.spin(odometry_motion_model)
#     rclpy.shutdown()
#
#
# if __name__ == '__main__':
#     main()


# CODE MOI: mo hinh chuyen dong odometry da sua.
import random
from math import atan2, cos, hypot, isfinite, pi, sin, sqrt, fabs

import rclpy
from geometry_msgs.msg import Pose, PoseArray
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf_transformations import euler_from_quaternion, quaternion_from_euler


def normalize(angle):
    """Dua goc ve khoang [-pi, pi]."""
    return atan2(sin(angle), cos(angle))


def angle_diff(a, b):
    a = atan2(sin(a), cos(a)) # chuyen doi goc tu 0 den 2*pi thanh goc tu -pi den pi
    b = atan2(sin(b), cos(b)) # chuyen doi goc tu 0 den 2*pi thanh goc tu -pi den pi
    d1 = a - b # tru truc tiep 2 goc de tim ra goc chenh lech
    d2 = 2 * pi - fabs(d1) # tinh goc chenh lech theo chieu nguoc lai cua 2 goc
    if d1 > 0: # neu goc chenh lech d1 > 0 thi goc chenh lech d2 se co gia tri am
        d2 *= -1.0
    if fabs(d1) < fabs(d2): # so sanh 2 goc chenh lech d1 va d2 de lay ra goc chenh lech nho hon
        return d1
    else:
        return d2


class OdometryMotionModel(Node):
    def __init__(self):
        super().__init__('odometry_motion_model')
        self.is_first_odom = True
        self.last_odom_x = 0.0
        self.last_odom_y = 0.0
        self.last_odom_theta = 0.0

        for name in ('alpha1', 'alpha2', 'alpha3', 'alpha4'):
            self.declare_parameter(name, 0.1)
        self.declare_parameter('nr_samples', 300)

        self.alpha1 = self.get_parameter('alpha1').value
        self.alpha2 = self.get_parameter('alpha2').value
        self.alpha3 = self.get_parameter('alpha3').value
        self.alpha4 = self.get_parameter('alpha4').value
        self.nr_samples = self.get_parameter('nr_samples').value

        if not all(
            isfinite(alpha) and alpha >= 0.0
            for alpha in (self.alpha1, self.alpha2, self.alpha3, self.alpha4)
        ):
            raise ValueError('alpha1..alpha4 must be finite and non-negative')
        if self.nr_samples <= 0:
            raise ValueError('nr_samples must be greater than zero')

        # Khoi tao bo sinh ngau nhien mot lan, khong seed lai moi callback.
        self.rng = random.Random()
        self.samples = PoseArray()
        self.samples.poses = [Pose() for _ in range(self.nr_samples)]
        for sample in self.samples.poses:
            sample.orientation.w = 1.0

        self.odom_sub_ = self.create_subscription(
            Odometry, 'bumperbot_controller/odom', self.odomCallback, 10
        )
        self.pose_array_pub_ = self.create_publisher(
            PoseArray, 'odometry_motion_model/samples', 10
        )

    def odomCallback(self, odom):
        position = odom.pose.pose.position
        orientation = odom.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([
            orientation.x, orientation.y, orientation.z, orientation.w
        ])
        self.samples.header.frame_id = odom.header.frame_id
        self.samples.header.stamp = odom.header.stamp

        if self.is_first_odom:
            # Cac hat bat dau tai pose odometry dau tien, trong cung frame.
            initial_q = quaternion_from_euler(0.0, 0.0, yaw)
            for sample in self.samples.poses:
                sample.position.x = position.x
                sample.position.y = position.y
                (
                    sample.orientation.x, sample.orientation.y,
                    sample.orientation.z, sample.orientation.w
                ) = initial_q
            self.is_first_odom = False
        else:
            dx = position.x - self.last_odom_x
            dy = position.y - self.last_odom_y
            delta_theta = angle_diff(yaw, self.last_odom_theta)
            delta_translation = hypot(dx, dy)

            # Chi bo qua huong tinh tien khi gan nhu khong di chuyen.
            # Nguong 1 cm co the lam mat huong khi lui tung buoc nho.
            if delta_translation < 0.01:
                delta_rot1 = 0.0
            else:
                delta_rot1 = angle_diff(atan2(dy, dx), self.last_odom_theta)
            delta_rot2 = angle_diff(delta_theta, delta_rot1)

            # Lui thang khong phai la quay that 180 do:
            # tinh nhieu quay doi xung cho chuyen dong tien va lui.
            rot1_magnitude = min(
                abs(delta_rot1), abs(angle_diff(delta_rot1, pi))
            )
            rot2_magnitude = min(
                abs(delta_rot2), abs(angle_diff(delta_rot2, pi))
            )

            # Phuong sai = tong cac thanh phan binh phuong.
            # random.gauss() nhan do lech chuan = sqrt(phuong sai).
            rot1_stddev = sqrt(
                self.alpha1 * rot1_magnitude**2
                + self.alpha2 * delta_translation**2
            )
            translation_stddev = sqrt(
                self.alpha3 * delta_translation**2
                + self.alpha4 * (rot1_magnitude**2 + rot2_magnitude**2)
            )
            rot2_stddev = sqrt(
                self.alpha1 * rot2_magnitude**2
                + self.alpha2 * delta_translation**2
            )

            for sample in self.samples.poses:
                delta_rot1_draw = angle_diff(
                    delta_rot1, self.rng.gauss(0.0, rot1_stddev)
                )
                delta_translation_draw = (
                    delta_translation - self.rng.gauss(0.0, translation_stddev)
                )
                delta_rot2_draw = angle_diff(
                    delta_rot2, self.rng.gauss(0.0, rot2_stddev)
                )

                _, _, sample_yaw = euler_from_quaternion([
                    sample.orientation.x, sample.orientation.y,
                    sample.orientation.z, sample.orientation.w
                ])
                sample.position.x += delta_translation_draw * cos(
                    sample_yaw + delta_rot1_draw
                )
                sample.position.y += delta_translation_draw * sin(
                    sample_yaw + delta_rot1_draw
                )
                new_yaw = normalize(
                    sample_yaw + delta_rot1_draw + delta_rot2_draw
                )
                q = quaternion_from_euler(0.0, 0.0, new_yaw)
                (
                    sample.orientation.x, sample.orientation.y,
                    sample.orientation.z, sample.orientation.w
                ) = q

        self.last_odom_x = position.x
        self.last_odom_y = position.y
        self.last_odom_theta = yaw
        self.pose_array_pub_.publish(self.samples)


def main():
    rclpy.init()
    node = None
    try:
        node = OdometryMotionModel()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
