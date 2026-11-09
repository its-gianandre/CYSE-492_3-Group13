
import time
import rclpy

from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped


FORWARD_SPEED = 0.05
DECISION_TIMEOUT = 3.0
MAX_TEST_DURATION = 30.0


class MotionController(Node):
    def __init__(self):
        super().__init__('motion_controller')

        self.publisher_ = self.create_publisher(
            TwistStamped, '/cmd_vel', 10
        )

        self.subscription = self.create_subscription(
            String,
            '/stop_sign_status',
            self.listener_callback,
            10
        )

        self.timer = self.create_timer(
            0.1, self.timer_callback
        )

        self.last_clear = None
        self.started = None
        self.stop_latched = False

    def listener_callback(self, msg):
        if self.stop_latched:
            return

        if msg.data == "CLEAR":
            now = time.monotonic()
            self.last_clear = now

            if self.started is None:
                self.started = now
        else:
            self.get_logger().info(f'Stopping: {msg.data}')
            self.stop_latched = True

    def send_velocity(self, linear=0.0):
        msg = TwistStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.twist.linear.x = float(linear)

        self.publisher_.publish(msg)

    def timer_callback(self):
        now = time.monotonic()

        if (self.last_clear is not None and
                now - self.last_clear > DECISION_TIMEOUT):
            self.stop_latched = True

        if (self.started is not None and
                now - self.started > MAX_TEST_DURATION):
            self.stop_latched = True

        if not self.stop_latched and self.last_clear is not None:
            self.send_velocity(FORWARD_SPEED)
        else:
            self.send_velocity(0.0)


def main():
    rclpy.init()
    node = MotionController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.send_velocity(0.0)
        time.sleep(0.2)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
