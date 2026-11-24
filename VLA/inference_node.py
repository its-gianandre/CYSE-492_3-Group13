# Gian Fernandez 10/23/26
# Read camera frames, run SmolVLA, and look for a red STOP sign.
# Used AI assistance

import re
import threading
import time

import cv2
import numpy as np
import pytesseract
import rclpy
from cv_bridge import CvBridge
from PIL import Image as PILImage
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, String

from turtlebot3_smolvla.vla_model import Predictor


def sees_stop_sign(rgb):
    """A basic demo detector: red octagon with the printed word STOP."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lower_red = cv2.inRange(hsv, (0, 90, 70), (12, 255, 255))
    upper_red = cv2.inRange(hsv, (168, 90, 70), (179, 255, 255))
    red = cv2.bitwise_or(lower_red, upper_red)
    height, width = rgb.shape[:2]
    # Fill white letters/holes so the outside edge looks like an octagon.
    size = max(5, int(min(height, width) * 0.026) | 1)
    red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((size, size), np.uint8))
    contours, _ = cv2.findContours(red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        if cv2.contourArea(contour) < width * height * 0.006:
            continue

        perimeter = cv2.arcLength(contour, True)
        sides = cv2.approxPolyDP(contour, 0.035 * perimeter, True)
        if not cv2.isContourConvex(sides) or not 6 <= len(sides) <= 10:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < 40 or h < 40 or not 0.7 < w / h < 1.4:
            continue

        crop = cv2.cvtColor(rgb[y:y+h, x:x+w], cv2.COLOR_RGB2GRAY)
        crop = cv2.resize(crop, None, fx=2, fy=2)
        text = pytesseract.image_to_string(crop, config="--psm 11").upper()
        if re.search(r"\bSTOP\b", re.sub(r"[^A-Z]+", " ", text)):
            return True

    return False


class InferenceNode(Node):
    def __init__(self):
        super().__init__("smolvla_inference")
        self.declare_parameter("image_topic", "/image_raw")
        topic = self.get_parameter("image_topic").value

        self.bridge = CvBridge()
        self.frame = None
        self.frame_time = 0.0
        self.frame_number = 0
        self.prompt = ""
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()
        self.stop_misses = 0
        self.stop_visible = False

        self.action_pub = self.create_publisher(String, "/vla/predicted_action", 10)
        self.sign_pub = self.create_publisher(Bool, "/vla/stop_sign_visible", 10)
        self.create_subscription(Image, topic, self.on_image, qos_profile_sensor_data)
        self.create_subscription(String, "/vla/mission_prompt", self.on_prompt, 10)

        self.predictor = Predictor()
        threading.Thread(target=self.inference_loop, daemon=True).start()
        threading.Thread(target=self.sign_loop, daemon=True).start()
        self.get_logger().info(f"Camera: {topic}; prompt topic: /vla/mission_prompt")

    def on_prompt(self, msg):
        with self.lock:
            self.prompt = msg.data.strip()
        self.get_logger().info(f"New mission prompt: {msg.data.strip()}")

    def on_image(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            with self.lock:
                self.frame = frame.copy()
                self.frame_time = time.monotonic()
                self.frame_number += 1
        except Exception as error:
            self.get_logger().error(f"Camera error: {error}")

    def get_frame(self):
        with self.lock:
            frame = self.frame
            prompt = self.prompt
            frame_time = self.frame_time
            frame_number = self.frame_number
        return frame, prompt, frame_time, frame_number

    def inference_loop(self):
        last_frame = -1
        while not self.shutdown_event.is_set():
            frame, prompt, frame_time, number = self.get_frame()
            if (frame is None or number == last_frame
                    or time.monotonic() - frame_time > 1.5):
                self.shutdown_event.wait(0.1)
                continue
            last_frame = number
            try:
                action = self.predictor.predict(PILImage.fromarray(frame), prompt)
                self.action_pub.publish(String(data=action))
                self.get_logger().info(f"Predicted: {action}")
            except Exception as error:
                self.get_logger().error(f"VLA error: {error}")
                self.shutdown_event.wait(0.5)

    def sign_loop(self):
        last_frame = -1
        while not self.shutdown_event.is_set():
            frame, _, frame_time, number = self.get_frame()
            if (frame is None or number == last_frame
                    or time.monotonic() - frame_time > 1.5):
                self.shutdown_event.wait(0.1)
                continue
            last_frame = number
            try:
                found = sees_stop_sign(frame)
                if found:
                    self.stop_visible = True
                    self.stop_misses = 0
                else:
                    self.stop_misses += 1
                    if self.stop_misses >= 3:
                        self.stop_visible = False
                self.sign_pub.publish(Bool(data=self.stop_visible))
            except Exception as error:
                self.get_logger().error(f"STOP detector error: {error}")
            self.shutdown_event.wait(0.25)


def main(args=None):
    rclpy.init(args=args)
    node = InferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown_event.set()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
