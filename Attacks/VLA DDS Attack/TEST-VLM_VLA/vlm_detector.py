# Only configured for stop sign detection 
import sys
import time
import cv2
import rclpy

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
            "Is a stop sign clearly visible in this image? "
            "Answer only YES or NO."
        )

        self.camera = Webcam(
            src=0, w=640, h=360, as_bgr=True
        )

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
                options={'temperature': 0}
            )

            answer = response.message.content.strip().upper()
            self.get_logger().info(f'Ollama answer: {answer}')

            if answer == "YES":
                self.publish_status("STOP")
                break

            elif answer == "NO":
                self.publish_status("CLEAR")

            else:
                self.publish_status("UNKNOWN")
                break

    def incoming(self, model_name):
        prompt = (
                    "Is a robot clearly visible in this image? "
                    "Answer only YES or NO."
                )
        
        self.camera = Webcam(
            src=0, w=640, h=360, as_bgr=True
                )
        
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
                options={'temperature': 0}
            )
        
            answer = response.message.content.strip().upper()
            self.get_logger().info(f'Ollama answer: {answer}')
        
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
