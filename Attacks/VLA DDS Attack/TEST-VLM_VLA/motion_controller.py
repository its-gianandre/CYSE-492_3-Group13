
import time
import rclpy

from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped


FORWARD_SPEED = 0.1
TURN_SPEED = 0.5
DECISION_TIMEOUT = 4.0
MAX_TEST_DURATION = 30.0
TURN_DURATION =  3.5
POST_TURN_FORWARD_DURATION = 4.0


class MotionController(Node):
    def __init__(self):
        super().__init__('motion_controller')

        # Publish movement commands
        self.publisher_ = self.create_publisher(
            TwistStamped, '/cmd_vel', 10
        )

        # Subscribe to detection status
        self.subscription = self.create_subscription(
            String,
            '/detection_status',
            self.listener_callback,
            10
        )

        self.timer = self.create_timer(
            0.1, self.timer_callback
        )

        self.last_clear = None
        self.started = None
        self.phase_started = None

        # Possible states:
        # WAITING, FORWARD, TURN_LEFT,
        # AVOID_FORWARD, STOPPED
        self.state = "WAITING"

    def listener_callback(self, msg):
        status = msg.data.strip().upper()
        now = time.monotonic()

        if self.state == "STOPPED":
            return

        if status == "CLEAR":
            # Only update normal forward movement
            if self.state in ("WAITING", "FORWARD"):
                self.last_clear = now

                if self.started is None:
                    self.started = now

                self.state = "FORWARD"

        elif status == "INCOMING":
            # Begin avoidance maneuver
            if self.state in ("WAITING", "FORWARD"):
                self.get_logger().info(
                    "Incoming robot detected. Turning left."
                )

                if self.started is None:
                    self.started = now

                self.phase_started = now
                self.state = "TURN_LEFT"
                self.send_velocity(0.0, 0.0)

        else:
            # STOP, UNKNOWN, or unexpected status
            self.get_logger().info(f'Stopping: {status}')
            self.state = "STOPPED"
            self.send_velocity(0.0, 0.0)

    def send_velocity(self, linear=0.0, angular=0.0):
        msg = TwistStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.twist.linear.x = float(linear)
        msg.twist.angular.z = float(angular)

        self.publisher_.publish(msg)

    def timer_callback(self):
        now = time.monotonic()

        # Maximum test duration
        if (self.started is not None and
                now - self.started > MAX_TEST_DURATION):
            self.state = "STOPPED"

        # Stop if no recent CLEAR during normal movement
        if self.state == "FORWARD":
            if (self.last_clear is None or
                    now - self.last_clear > DECISION_TIMEOUT):
                self.state = "WAITING"

        if self.state == "FORWARD":
            self.send_velocity(FORWARD_SPEED, 0.0)

        elif self.state == "TURN_LEFT":
            if now - self.phase_started < TURN_DURATION:
                self.send_velocity(0.0, TURN_SPEED)
            else:
                self.get_logger().info(
                    "Turn complete. Moving forward."
                )

                self.phase_started = now
                self.state = "AVOID_FORWARD"
                self.send_velocity(FORWARD_SPEED, 0.0)

        elif self.state == "AVOID_FORWARD":
            if (now - self.phase_started <
                    POST_TURN_FORWARD_DURATION):
                self.send_velocity(FORWARD_SPEED, 0.0)
            else:
                self.get_logger().info(
                    "Avoidance maneuver complete."
                )

                self.state = "STOPPED"
                self.send_velocity(0.0, 0.0)

        else:
            self.send_velocity(0.0, 0.0)


def main():
    rclpy.init()
    node = MotionController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.send_velocity(0.0, 0.0)
        time.sleep(0.2)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
