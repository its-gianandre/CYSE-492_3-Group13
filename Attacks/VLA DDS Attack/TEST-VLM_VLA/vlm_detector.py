
import sys
import time
import cv2
import rclpy
import json

from ollama import chat
from webcam import Webcam
from rclpy.node import Node
from std_msgs.msg import String


class VLMDetector(Node):
    def __init__(self):
        super().__init__('vlm_detector')

        self.publisher_ = self.create_publisher(
            String, '/detection_status', 10
        )

        self.camera = None

    def publish_status(self, status):
        msg = String()
        msg.data = status
        self.publisher_.publish(msg)
        self.get_logger().info(f'Detection status: {status}')

    # Test 1: Stop sign detection
    def run(self, model_name):
        prompt = (
            "Look at this image. Is there a stop sign visible? "
            "Respond only with a JSON object containing the key "
            "'answer' and a value of either 'YES' or 'NO'. "
            "Do not provide explanations."
        )

        self.camera = Webcam(
            src=0, w=1080, h=1920, as_bgr=True
        )

        time.sleep(1)

        while rclpy.ok():
            grabbed, frame = self.camera.read()

            if not grabbed:
                raise RuntimeError("Camera did not return a frame")

            success, buffer = cv2.imencode(".jpg", frame)

            if not success:
                raise RuntimeError("Could not encode frame")

            response = chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [buffer.tobytes()]
                }],
                format={
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "enum": ["YES", "NO"]
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                },
                options={
                    'temperature': 0,
                    'num_predict': 64
                }
            )

            # Get raw response
            raw_answer = response.message.content
            self.get_logger().info(
                f'Ollama raw response: {raw_answer}'
            )

            # Extract answer from JSON
            try:
                result = json.loads(raw_answer)
                answer = result["answer"].strip().upper()

                if answer not in ("YES", "NO"):
                    answer = "INVALID"

            except (
                json.JSONDecodeError,
                KeyError,
                AttributeError,
                TypeError
            ):
                answer = "INVALID"

            self.get_logger().info(f'Ollama answer: {answer}')

            # Publish status
            if answer == "YES":
                self.publish_status("STOP")
                break

            elif answer == "NO":
                self.publish_status("CLEAR")

            else:
                self.publish_status("UNKNOWN")
                break

    # Test 2: Incoming robot detection
    def incoming(self, model_name):
        prompt = (
            "Look at this image. Is another mobile robot clearly "
            "visible directly ahead in the path? "
            "Respond with YES if a robot is visible, otherwise NO. "
            "Return your answer in JSON using the key 'answer'. "
            "Do not provide explanations."
        )

        self.camera = Webcam(
            src=0, w=1080, h=1920, as_bgr=True
        )

        time.sleep(1)

        while rclpy.ok():
            grabbed, frame = self.camera.read()

            if not grabbed:
                raise RuntimeError("Camera did not return a frame")

            success, buffer = cv2.imencode(".jpg", frame)

            if not success:
                raise RuntimeError("Could not encode frame")

            response = chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [buffer.tobytes()]
                }],
                format={
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "enum": ["YES", "NO"]
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                },
                options={
                    'temperature': 0,
                    'num_predict': 64
                }
            )

            # Get raw response
            raw_answer = response.message.content
            self.get_logger().info(
                f'Ollama raw response: {raw_answer}'
            )

            # Try extracting answer from JSON
            try:
                result = json.loads(raw_answer)

                if isinstance(result, dict):
                    value = result.get("answer", "")

                    if isinstance(value, str):
                        answer = value.strip().lower()
                    else:
                        answer = ""
                else:
                    answer = raw_answer.strip().lower()

            except (json.JSONDecodeError, TypeError):
                answer = raw_answer.strip().lower()

            # Remove extra punctuation
            answer = answer.strip(" \n\t.!?,\"'")

            # Word bank for detecting robots
            keywords = (
                "robot",
                "robotic",
                "turtlebot"
            )

            # Negative responses
            negatives = (
                "no robot",
                "no robotic",
                "no turtlebot",
                "no visible robot",
                "don't see a robot",
                "do not see a robot",
                "can't see a robot",
                "cannot see a robot",
                "robot is not visible",
                "robot isn't visible",
                "not a robot"
            )

            # Uncertain responses
            uncertain = (
                "maybe",
                "unsure",
                "uncertain",
                "unclear",
                "not sure",
                "cannot tell",
                "can't tell"
            )

            # Interpret response
            if answer in ("yes", "no"):
                answer = answer.upper()

            elif any(word in answer for word in uncertain):
                answer = "INVALID"

            elif any(phrase in answer for phrase in negatives):
                answer = "NO"

            elif any(word in answer for word in
                     ("not", "no ", "without",
                      "cannot", "can't", "don't")):
                answer = "INVALID"

            elif answer.startswith(("yes ", "yes,")):
                answer = "YES"

            elif any(word in answer for word in keywords):
                answer = "YES"

            else:
                answer = "INVALID"

            self.get_logger().info(f'Ollama answer: {answer}')

            # Publish status
            if answer == "YES":
                self.publish_status("INCOMING")
                break

            elif answer == "NO":
                self.publish_status("CLEAR")

            else:
                self.publish_status("UNKNOWN")
                break

    def crossing(self, model_name):
        prompt = (
            "Look at this image. Is there a robot visible? "
            "Respond only with a JSON object containing the key "
            "'answer' and a value of either 'YES' or 'NO'. "
            "Do not provide explanations."
        )

        self.camera = Webcam(
            src=0, w=1080, h=1920, as_bgr=True
        )

        time.sleep(1)

        while rclpy.ok():
            grabbed, frame = self.camera.read()

            if not grabbed:
                raise RuntimeError("Camera did not return a frame")

            success, buffer = cv2.imencode(".jpg", frame)

            if not success:
                raise RuntimeError("Could not encode frame")

            response = chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [buffer.tobytes()]
                }],
                format={
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "enum": ["YES", "NO"]
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                },
                options={
                    'temperature': 0,
                    'num_predict': 64
                }
            )

            # Get raw response
            raw_answer = response.message.content
            self.get_logger().info(
                f'Ollama raw response: {raw_answer}'
            )

            # Extract answer from JSON
            try:
                result = json.loads(raw_answer)
                answer = result["answer"].strip().upper()

                if answer not in ("YES", "NO"):
                    answer = "INVALID"

            except (
                json.JSONDecodeError,
                KeyError,
                AttributeError,
                TypeError
            ):
                answer = "INVALID"

            self.get_logger().info(f'Ollama answer: {answer}')

            # Publish status
            if answer == "YES":
                self.publish_status("STOP")
                break

            elif answer == "NO":
                self.publish_status("CLEAR")

            else:
                self.publish_status("UNKNOWN")
                break        



def main():
    # Validate terminal arguments
    if len(sys.argv) != 3 or sys.argv[2] not in (
        "stopsign", "incoming_test"
    ):
        print(
            "Usage: ros2 run vlm_turtlebot vlm_detector "
            "<model> <stopsign|incoming_test>"
        )
        return

    model_name = sys.argv[1]
    test_type = sys.argv[2]

    rclpy.init()
    node = VLMDetector()

    try:
        if test_type == "stopsign":
            node.run(model_name)

        elif test_type == "incoming_test":
            node.incoming(model_name)

    except KeyboardInterrupt:
        node.get_logger().info("Detection interrupted")

        if rclpy.ok():
            node.publish_status("STOP")

    except Exception as error:
        node.get_logger().error(
            f"Detection failed: {error}"
        )

        if rclpy.ok():
            node.publish_status("STOP")

    finally:
        time.sleep(0.2)

        if node.camera is not None:
            node.camera.release()

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
