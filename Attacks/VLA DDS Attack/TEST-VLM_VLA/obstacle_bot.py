# Script for running the obstacle bot forward (ROS 2 Humble)

import sys
import time
import rclpy
from geometry_msgs.msg import Twist

speed = float(sys.argv[1]) # Speed in m/s
duration = float(sys.argv[2]) # Duration in seconds

rclpy.init()
node = rclpy.create_node("move_forward")
publisher = node.create_publisher(Twist, "/cmd_vel", 10)

msg = Twist()
msg.linear.x = speed

time.sleep(1)

try:
    end_time = time.monotonic() + duration

    while time.monotonic() < end_time:
        publisher.publish(msg)
        time.sleep(0.1)

finally:
    msg.linear.x = 0.0
    publisher.publish(msg)
    time.sleep(0.5)
    node.destroy_node()
    rclpy.shutdown()
