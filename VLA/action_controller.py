"""
Gian Fernandez 10/23/26
TurtleBot3 square-path demo with STOP-sign override.

Forward one side, rotate clockwise by 90 degrees, and repeat.
STOP-sign detection pauses the route and sends an all-zero Twist.
The saved mission resumes after the sign has been absent for two seconds.
"""

import math
import re
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Bool, String

ACTION = re.compile(r"^(forward|backward|left|right|stop)_(\d+(?:\.\d+)?)_(\d+(?:\.\d+)?)s$")


def yaw_from_quaternion(q):
    return math.atan2(
        2 * (q.w * q.z + q.x * q.y),
        1 - 2 * (q.y * q.y + q.z * q.z),
    )


def angle_change(new, old):
    """Signed change in angle, including across +/- 180 degrees."""
    return math.atan2(math.sin(new - old), math.cos(new - old))


class ActionController(Node):
    def __init__(self):
        super().__init__("smolvla_action_controller")
        self.declare_parameter("dry_run", True)
        self.declare_parameter("stamped", True)
        self.declare_parameter("side_m", 0.30)
        self.declare_parameter("forward_speed", 0.07)
        self.declare_parameter("turn_speed", 0.4)
        self.declare_parameter("robot_max_linear", 0.22)
        self.declare_parameter("robot_max_angular", 2.84)

        def parameter(name):
            return self.get_parameter(name).value

        self.dry_run = bool(parameter("dry_run"))
        self.stamped = bool(parameter("stamped"))
        self.side_m = float(parameter("side_m"))
        self.forward_speed = float(parameter("forward_speed"))
        self.turn_speed = float(parameter("turn_speed"))
        self.max_linear = float(parameter("robot_max_linear"))
        self.max_angular = float(parameter("robot_max_angular"))

        values = [self.side_m, self.forward_speed, self.turn_speed,
                  self.max_linear, self.max_angular]
        if any(not math.isfinite(x) or x <= 0 for x in values):
            raise ValueError("Distances and speed limits must be positive")
        if self.forward_speed > self.max_linear or self.turn_speed > self.max_angular:
            raise ValueError("Mission speed exceeds configured robot rating")

        topic = "/vla/debug_cmd_vel" if self.dry_run else "/cmd_vel"
        msg_type = TwistStamped if self.stamped else Twist
        self.vel_pub = self.create_publisher(msg_type, topic, 10)

        self.create_subscription(Bool, "/vla/enable", self.on_enable, 10)
        self.create_subscription(String, "/vla/mission_prompt", self.on_prompt, 10)
        self.create_subscription(String, "/vla/predicted_action", self.on_action, 10)
        self.create_subscription(Bool, "/vla/stop_sign_visible", self.on_sign, 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos_profile_sensor_data)

        self.armed = False
        self.prompt = ""
        self.phase = "IDLE"  # IDLE, FORWARD, TURN

        self.position = None
        self.yaw = None
        self.odom_time = 0.0
        self.side_start = None  # x, y, heading at start of each straight side
        self.previous_yaw = None
        self.right_turn_degrees = 0.0
        self.completed_sides = 0

        self.sign_visible = False
        self.sign_time = 0.0
        self.stop_latched = False
        self.clear_since = None
        self.clear_delay = 2.0

        self.manual_linear = 0.0
        self.manual_angular = 0.0
        self.manual_until = 0.0

        self.create_timer(0.05, self.tick)  # 20 Hz control loop
        self.get_logger().info(
            f"DISARMED; output={topic}; SQUARE DEMO ACTIVE; STOP OVERRIDE ENABLED"
        )

    def drive(self, linear=0.0, angular=0.0):
        """Publish a fresh velocity message, explicitly setting ALL six values."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"
            twist = msg.twist
        else:
            msg = Twist()
            twist = msg

        twist.linear.x = float(linear)
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = float(angular)
        self.vel_pub.publish(msg)

    def disarm(self, reason="Manually disarmed"):
        self.armed = False
        self.manual_until = 0.0
        self.drive()  # All six velocity values zero
        self.get_logger().warn(reason)

    def on_enable(self, msg):
        if not msg.data:
            self.disarm()
            return
        if not self.armed:
            self.armed = True
            self.drive()
            if self.prompt:
                self.start_square()
            self.get_logger().warn("ARMED; use /vla/enable false to stop")

    def on_prompt(self, msg):
        text = msg.data.strip()
        lower = text.lower()
        if lower in ("stop", "cancel", "disarm"):
            self.prompt = ""
            self.phase = "IDLE"
            self.disarm("Mission cancelled")
            return

        # Supports the square demo prompt and the earlier forward/right demo wording.
        square = "square" in lower and "stop" in lower
        previous_demo = all(word in lower for word in ("forward", "right", "stop sign"))
        if not (square or previous_demo):
            self.prompt = ""
            self.phase = "IDLE"
            self.disarm(f"Unsupported mission prompt: {text!r}")
            return

        self.prompt = text
        self.start_square()
        self.get_logger().info(f"Saved repeating-square mission: {text}")

    def start_square(self):
        self.drive()
        self.phase = "FORWARD"
        self.side_start = (
            (self.position[0], self.position[1], self.yaw)
            if self.position is not None and self.yaw is not None
            else None
        )
        self.previous_yaw = self.yaw
        self.right_turn_degrees = 0.0
        self.completed_sides = 0
        self.manual_until = 0.0

    def on_odom(self, msg):
        p = msg.pose.pose.position
        heading = yaw_from_quaternion(msg.pose.pose.orientation)
        if self.phase == "TURN" and self.previous_yaw is not None:
            # Right (clockwise) rotation contributes positive progress.
            delta = math.degrees(angle_change(heading, self.previous_yaw))
            self.right_turn_degrees -= delta
        self.previous_yaw = heading
        self.yaw = heading
        self.position = (p.x, p.y)
        self.odom_time = time.monotonic()
        if self.phase == "FORWARD" and self.side_start is None:
            self.side_start = (p.x, p.y, heading)

    def on_sign(self, msg):
        now = time.monotonic()
        self.sign_time = now
        self.sign_visible = bool(msg.data)

        if self.sign_visible:
            if not self.stop_latched:
                self.get_logger().warn("STOP SIGN: publishing ALL-ZERO velocity")
            self.stop_latched = True
            self.clear_since = None
            self.manual_until = 0.0
            self.drive()  # Immediate zero on sign callback
        elif self.stop_latched and self.clear_since is None:
            self.clear_since = now
            self.get_logger().info("Sign absent; confirming for 2 seconds")

    def stopping(self, now):
        # Missing camera detection messages also cause a stop.
        if now - self.sign_time > 2.0:
            return True
        if self.sign_visible:
            return True
        if self.stop_latched:
            if self.clear_since is None or now - self.clear_since < self.clear_delay:
                return True
            self.stop_latched = False
            self.clear_since = None
            self.get_logger().info("STOP sign cleared; resuming square")
        return False

    def on_action(self, msg):
        if not self.armed:
            return

        text = msg.data.strip().lower()
        match = ACTION.fullmatch(text)
        if match is None:
            self.disarm(f"Invalid VLA action: {text!r}")
            return
        direction, speed_text, duration_text = match.groups()
        speed, duration = float(speed_text), float(duration_text)
        if (not math.isfinite(speed) or not math.isfinite(duration)
                or speed < 0 or duration <= 0):
            self.disarm("Invalid VLA speed/duration")
            return

        if self.stopping(time.monotonic()):
            self.drive()
            return

        if self.prompt:
            # The square route is determined by odometry, not single-action predictions.
            return

        if direction == "stop":
            self.manual_until = 0.0
            self.drive()
            return
        if speed <= 0:
            self.disarm("Zero movement speed")
            return

        linear = speed if direction == "forward" else -speed if direction == "backward" else 0.0
        angular = speed if direction == "left" else -speed if direction == "right" else 0.0
        if abs(linear) > self.max_linear or abs(angular) > self.max_angular:
            self.disarm("Action exceeds robot's configured rated speed")
            return
        self.manual_linear = linear
        self.manual_angular = angular
        self.manual_until = time.monotonic() + duration
        self.drive(linear, angular)

    def tick(self):
        if not self.armed:
            self.drive()
            return

        now = time.monotonic()
        if self.stopping(now):
            self.drive()  # STOP has priority over EVERY movement phase
            return

        if not self.prompt:
            if now < self.manual_until:
                self.drive(self.manual_linear, self.manual_angular)
            else:
                self.drive()
            return

        if now - self.odom_time > 1.5 or self.position is None or self.yaw is None:
            self.drive()  # No odometry = no route movement
            return

        if self.phase == "FORWARD":
            if self.side_start is None:
                self.side_start = (*self.position, self.yaw)
            start_x, start_y, start_heading = self.side_start
            delta_x = self.position[0] - start_x
            delta_y = self.position[1] - start_y
            # Distance along the heading at the start of this side.
            distance = delta_x * math.cos(start_heading) + delta_y * math.sin(start_heading)

            if distance < self.side_m:
                self.drive(self.forward_speed, 0.0)
            else:
                self.completed_sides += 1
                self.phase = "TURN"
                self.right_turn_degrees = 0.0
                self.previous_yaw = self.yaw
                self.drive()
                self.get_logger().info(
                    f"Finished side {self.completed_sides}; turning RIGHT 90 degrees"
                )

        elif self.phase == "TURN":
            remaining = 90.0 - self.right_turn_degrees
            if remaining <= 2.5:
                self.phase = "FORWARD"
                self.side_start = (*self.position, self.yaw)
                self.drive()
                self.get_logger().info("Right turn finished; moving forward again")
            else:
                # Rotate in place, slowing near the target heading.
                turn = min(self.turn_speed, max(0.08, math.radians(remaining) * 0.8))
                self.drive(0.0, -turn)
        else:
            self.drive()


def main(args=None):
    rclpy.init(args=args)
    node = ActionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.disarm("Controller shutting down")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
