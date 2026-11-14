# Script for running the obstacle bot forward 
import sys
import time
import rclpy
from geometry_msgs.msg import TwistStamped

speed = float(sys.argv[1]) # Speed in m/s
duration = float(sys.argv[2]) # Duration of time in seconds

rclpy.init()
node = rclpy.create_node("move_forward")
publisher = node.create_publisher(TwistStamped, "/cmd_vel", 10)

msg = TwistStamped()
msg.twist.linear.x = speed

time.sleep(1)

try:
    end_time = time.monotonic() + duration

    while time.monotonic() < end_time:
        msg.header.stamp = node.get_clock().now().to_msg()
        publisher.publish(msg)
        time.sleep(0.1)

finally:
    msg.twist.linear.x = 0.0

    for i in range(5):
        msg.header.stamp = node.get_clock().now().to_msg()
        publisher.publish(msg)
        time.sleep(0.1)

    node.destroy_node()
    rclpy.shutdown()
