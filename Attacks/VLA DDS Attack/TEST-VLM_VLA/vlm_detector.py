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
            String, '/stop_sign_status', 10
        )
        self.camera = None

    def publish_status(self, status):
        msg = String()
        msg.data = status
        self.publisher_.publish(msg)
        self.get_logger().info(f'Detection status: {status}')

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
        time.sleep(1) # Added delay to avoid detecting stop sign immediately
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
                options={'temperature': 0, "num_predict": 64}
            )

            # Get the raw response from Ollama
            raw_answer = response.message.content
            self.get_logger().info(f'Ollama raw response: {raw_answer}')

            # Extract the answer from the JSON response
            try:
                result = json.loads(raw_answer)
                answer = result["answer"].strip().upper()

                if answer not in ("YES", "NO"):
                    answer = "INVALID"

            except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
                answer = "INVALID"

            self.get_logger().info(f'Ollama answer: {answer}')    
            # Publish the appropriate status
            if answer == "YES":
                self.publish_status("STOP")
                break
            
            elif answer == "NO":
                self.publish_status("CLEAR")
            
            else:
                self.publish_status("UNKNOWN")
                break    

def main():
    if len(sys.argv) != 3 or sys.argv[2] != "stopsign":
        print("Usage: ros2 run vlm_turtlebot vlm_detector <model> stopsign")
        return

    rclpy.init()
    node = VLMDetector()

    try:
        node.run(sys.argv[1])

    except KeyboardInterrupt:
        node.get_logger().info("Detection interrupted")

    except Exception as error:
        node.get_logger().error(f"Detection failed: {error}")

    finally:
        node.publish_status("STOP")
        time.sleep(0.2)

        if node.camera is not None:
            node.camera.release()

        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
