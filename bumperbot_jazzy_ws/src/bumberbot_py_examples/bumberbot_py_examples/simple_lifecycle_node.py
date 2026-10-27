# =========================
# 1. IMPORT CÁC THƯ VIỆN
# =========================

# Thư viện chính để sử dụng ROS 2 với Python
import rclpy

# Import Node dành cho Lifecycle Node.
# Node này có state machine để quản lý các trạng thái:
# unconfigured -> inactive -> active -> ...
from rclpy.lifecycle import Node

# Import executor để ROS 2 có thể chờ và xử lý các callback
# như subscriber callback, lifecycle callback,...
import rclpy.executors

# State:
#   Đại diện cho trạng thái của Lifecycle Node.
#
# TransitionCallbackReturn:
#   Giá trị trả về của các hàm lifecycle như:
#   on_configure(), on_activate(),...
#
# Ví dụ:
#   TransitionCallbackReturn.SUCCESS
# nghĩa là quá trình chuyển trạng thái thành công.
from rclpy.lifecycle import State, TransitionCallbackReturn

# Kiểu message String của ROS 2
# Dùng để nhận dữ liệu dạng chuỗi từ topic "chatter"
from std_msgs.msg import String

# Thư viện Python thông thường
# ở đây dùng time.sleep()
import time


# ==========================================================
# 2. TẠO CLASS LIFECYCLE NODE
# ==========================================================

# SimpleLifecycleNode kế thừa Node của rclpy.lifecycle
#
# Vì vậy class này có:
# - các chức năng Node ROS 2 thông thường
# - Lifecycle State Machine
# - các callback lifecycle:
#       on_configure()
#       on_activate()
#       on_deactivate()
#       on_cleanup()
#       on_shutdown()
#
class SimpleLifecycleNode(Node):

    # ======================================================
    # CONSTRUCTOR
    # ======================================================

    # __init__ được chạy khi object SimpleLifecycleNode được tạo.
    #
    # node_name:
    #   tham số nhận tên node.
    #
    # **kwargs:
    #   nhận thêm các keyword argument khác.
    #
    # Ví dụ:
    # SimpleLifecycleNode(
    #     'simple_lifecycle_node',
    #     namespace='/robot'
    # )
    #
    def __init__(self, node_name, **kwargs):

        # Gọi constructor của class cha (Lifecycle Node)
        #
        # Việc này giúp ROS 2:
        # - tạo Node
        # - tạo Lifecycle State Machine
        # - tạo các Lifecycle Service
        # - quản lý trạng thái của node
        #
        # Lưu ý:
        # mặc dù __init__ có tham số node_name,
        # code hiện tại vẫn đặt cố định tên node là:
        #
        # 'simple_lifecycle_node'
        #
        super().__init__('simple_lifecycle_node', **kwargs)
        # kwargs dùng để nhận thêm các tham số khác


    # ======================================================
    # 3. CONFIGURE CALLBACK
    # ======================================================

    # Hàm này KHÔNG phải do ta tự gọi.
    #
    # ROS 2 Lifecycle State Machine sẽ tự gọi hàm này
    # khi có transition "configure".
    #
    # Ví dụ:
    #
    # ros2 lifecycle set /simple_lifecycle_node configure
    #
    # Luồng trạng thái:
    #
    # unconfigured
    #       |
    #       | configure
    #       v
    # configuring
    #       |
    #       | on_configure()
    #       v
    # inactive
    #
    # state: State
    #   state là object được ROS 2 tự động truyền vào.
    #
    # -> TransitionCallbackReturn
    #   type hint cho biết hàm này trả về kết quả của transition.
    #
    def on_configure(self, state: State) -> TransitionCallbackReturn:

        # Tạo Subscriber
        #
        # String:
        #   kiểu message muốn nhận.
        #
        # "chatter":
        #   tên topic muốn subscribe.
        #
        # self.msgCallback:
        #   callback được gọi khi có message mới.
        #
        # 10:
        #   QoS depth.
        #   Có thể hiểu đơn giản là hàng đợi giữ tối đa
        #   10 message chưa được xử lý.
        #
        self.sub_ = self.create_subscription(
            String,
            "chatter",
            self.msgCallback,
            10
        )

        # Tôi muốn nhận msg kiểu String từ topic chatter.
        # Mỗi khi có tin nhắn thì ROS 2 gọi self.msgCallback.
        # Hàng đợi chứa tối đa 10 tin chưa xử lý.

        # In thông báo ra terminal
        self.get_logger().info(
            "Lifrcycle node on_configure() called"
        )

        # Báo cho Lifecycle State Machine rằng
        # quá trình configure đã thành công.
        #
        # Nếu thành công:
        #
        # configuring -> inactive
        #
        return TransitionCallbackReturn.SUCCESS
        # thông báo cho ROS2 biết chuyển trạng thái thành công


    # ======================================================
    # 4. SHUTDOWN CALLBACK
    # ======================================================

    # Được ROS 2 gọi khi có shutdown transition.
    #
    # Ví dụ:
    #
    # ros2 lifecycle set /simple_lifecycle_node shutdown
    #
    # Có thể shutdown node từ nhiều trạng thái khác nhau.
    #
    def on_shutdown(self, state: State) -> TransitionCallbackReturn:

        # được ROS2 gọi khi shutdown transition

        # Hủy subscriber đã tạo trong on_configure().
        #
        # Sau dòng này node không còn subscribe topic chatter nữa.
        #
        self.destroy_subscription(self.sub_)

        # Lưu ý:
        # destroy_subscription() là hàm của Node.
        # Không phải subscriber gọi hàm này,
        # mà chính code của chúng ta yêu cầu Node hủy subscriber.
        #
        # khi hàm này được subscriber gọi sẽ hủy subscription

        # In thông báo
        self.get_logger().info(
            "Lifecycle node on_shutdown() called"
        )

        # Báo cho state machine biết shutdown thành công
        return TransitionCallbackReturn.SUCCESS


    # ======================================================
    # 5. CLEANUP CALLBACK
    # ======================================================

    # on_cleanup() thường được gọi khi:
    #
    # inactive
    #    |
    #    | cleanup
    #    v
    # cleaningup
    #    |
    #    | on_cleanup()
    #    v
    # unconfigured
    #
    # Mục đích:
    # giải phóng những resource được tạo trong on_configure().
    #
    def on_cleanup(self, state: State) -> TransitionCallbackReturn:

        # Subscriber được tạo khi configure.
        #
        # Khi cleanup thì ta hủy subscriber đó.
        self.destroy_subscription(self.sub_)

        # In thông báo
        self.get_logger().info(
            "Lifecycle node on_cleanup() called"
        )

        # Báo cleanup thành công
        return TransitionCallbackReturn.SUCCESS


    # ======================================================
    # 6. ACTIVATE CALLBACK
    # ======================================================

    # Được ROS 2 Lifecycle State Machine gọi khi transition:
    #
    # inactive
    #     |
    #     | activate
    #     v
    # activating
    #     |
    #     | on_activate()
    #     v
    # active
    #
    # Ví dụ terminal:
    #
    # ros2 lifecycle set /simple_lifecycle_node activate
    #
    def on_activate(self, state: State) -> TransitionCallbackReturn:

        # In thông báo rằng callback activate đang được gọi
        self.get_logger().info(
            "Lifecycle node on_activate() called"
        )

        # Dừng thread hiện tại trong 2 giây.
        #
        # Vì chương trình dùng SingleThreadedExecutor,
        # trong 2 giây này executor không thể xử lý callback khác
        # trên cùng thread.
        #
        time.sleep(2)

        # Gọi on_activate() của class cha.
        #
        # super():
        #   truy cập class cha của SimpleLifecycleNode.
        #
        # state:
        #   chính là object State mà ROS 2 truyền vào
        #   khi callback này được gọi.
        #
        # Class cha sẽ thực hiện logic activate mặc định
        # của Lifecycle Node.
        #
        return super().on_activate(state)


    # ======================================================
    # 7. DEACTIVATE CALLBACK
    # ======================================================

    # Được gọi khi node chuyển:
    #
    # active
    #    |
    #    | deactivate
    #    v
    # deactivating
    #    |
    #    | on_deactivate()
    #    v
    # inactive
    #
    # Ví dụ:
    #
    # ros2 lifecycle set /simple_lifecycle_node deactivate
    #
    def on_deactivate(self, state: State) -> TransitionCallbackReturn:

        # In thông báo
        self.get_logger().info(
            "Lifecycle node on_deactivate() called"
        )

        # Gọi hàm on_deactivate() mặc định của class cha.
        #
        # state được ROS 2 truyền vào tự động.
        #
        return super().on_deactivate(state)


    # ======================================================
    # 8. SUBSCRIBER CALLBACK
    # ======================================================

    # Hàm này cũng KHÔNG phải chúng ta tự gọi.
    #
    # Nó được ROS 2 gọi khi subscriber nhận được message
    # từ topic "chatter".
    #
    # Luồng:
    #
    # Publisher
    #     |
    #     v
    # /chatter
    #     |
    #     v
    # Subscriber
    #     |
    #     v
    # msgCallback(msg)
    #
    # msg:
    #   message ROS 2 tự động truyền vào.
    #
    def msgCallback(self, msg):

        # Lấy trạng thái hiện tại từ Lifecycle State Machine.
        #
        # self._state_machine:
        #   state machine của Lifecycle Node.
        #
        # current_state:
        #   trạng thái hiện tại.
        #
        current_state = self._state_machine.current_state

        # lấy trạng thái của lifecycle hiện tại

        # current_state thường có dạng:
        #
        # (id, label)
        #
        # Ví dụ:
        #
        # (3, "active")
        #
        # current_state[0]
        #     -> ID của state
        #
        # current_state[1]
        #     -> tên/label của state
        #
        # thường nhận dạng theo kiểu (id, label),
        # current_state[1] nghĩa là lấy label


        # Chỉ xử lý message nếu Lifecycle Node
        # đang ở trạng thái "active".
        #
        # Nếu node đang inactive:
        #
        # callback vẫn có thể được gọi,
        # nhưng đoạn bên trong if sẽ không chạy.
        #
        if current_state[1] == "active":

            # In dữ liệu nhận được.
            #
            # Ví dụ publisher gửi:
            #
            # data: "hello"
            #
            # Terminal sẽ hiện:
            #
            # I heard: hello
            #
            self.get_logger().info(
                "I heard: %s" % msg.data
            )


# ==========================================================
# 9. HÀM MAIN
# ==========================================================

# Đây là hàm chính dùng để khởi động ROS 2 node.
#
def main():

    # Khởi tạo ROS 2 Python client library.
    #
    # Phải gọi rclpy.init() trước khi tạo Node.
    #
    rclpy.init()


    # ======================================================
    # TẠO EXECUTOR
    # ======================================================

    # Executor chịu trách nhiệm:
    #
    # - chờ message
    # - gọi subscriber callback
    # - xử lý service
    # - xử lý timer
    # - xử lý Lifecycle transition
    #
    # SingleThreadedExecutor:
    #
    # chỉ sử dụng 1 thread để xử lý callback.
    #
    executor = rclpy.executors.SingleThreadedExecutor()


    # ======================================================
    # TẠO LIFECYCLE NODE
    # ======================================================

    # Tạo object từ class SimpleLifecycleNode.
    #
    # Khi dòng này chạy:
    #
    # SimpleLifecycleNode.__init__()
    #
    # sẽ được gọi.
    #
    simple_lifecycle_node = SimpleLifecycleNode(
        'simple_lifecycle_node'
    )


    # ======================================================
    # THÊM NODE VÀO EXECUTOR
    # ======================================================

    # Báo cho executor:
    #
    # "Hãy quản lý và xử lý callback của node này."
    #
    executor.add_node(simple_lifecycle_node)


    # ======================================================
    # CHẠY EXECUTOR
    # ======================================================

    try:

        # spin() làm chương trình chạy liên tục.
        #
        # Có thể tưởng tượng gần giống:
        #
        # while ROS2 đang chạy:
        #
        #     chờ event
        #
        #     nếu message đến:
        #         gọi msgCallback()
        #
        #     nếu configure:
        #         gọi on_configure()
        #
        #     nếu activate:
        #         gọi on_activate()
        #
        #     ...
        #
        executor.spin()


    # ======================================================
    # XỬ LÝ KHI CHƯƠNG TRÌNH DỪNG
    # ======================================================

    # KeyboardInterrupt:
    #   xảy ra khi nhấn Ctrl + C.
    #
    # ExternalShutdownException:
    #   xảy ra nếu ROS context bị shutdown từ bên ngoài.
    #
    except (
        KeyboardInterrupt,
        rclpy.executors.ExternalShutdownException
    ):

        # Hủy Node và giải phóng tài nguyên của Node
        simple_lifecycle_node.destroy_node()


# ==========================================================
# 10. ĐIỂM BẮT ĐẦU CHƯƠNG TRÌNH
# ==========================================================

# Khi chạy trực tiếp:
#
# python3 ten_file.py
#
# Python đặt:
#
# __name__ = '__main__'
#
# nên main() được gọi.
#
# Nếu file này chỉ được import bởi file Python khác,
# main() sẽ không tự động chạy.
#
if __name__ == '__main__':
     main()