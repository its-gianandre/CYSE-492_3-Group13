from ollama import chat, ChatResponse
from webcam import Webcam
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from threading import Thread

import rclpy
import cv2
import sys
import time

#if we use the camera here we don't need a camera node - simplier
camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution

#need to be able to use terminal args to select the model and then select the test
#i believe we had 5 VLMs on the AGX
#there are 3 tests: stop sign, oncoming traffic, perpendicular traffic


# Choosing the model 
# Continously prompt it like before for whatever we are looking for (e.g. Do you see a stop sign?)
# Read the tokens, and see if it responds saying it sees a stop sign
# It should return something that allows us to tell if it can actually see a stop sign (e.g. Boolean)
# When it returns true or whatever value, it will output a command velocity of zero. 

# Send velocity commands to ROS velocity node
def send_velocity(node, publisher, linear=0.0, angular=0.0):
    msg = TwistStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = "base_link"
    msg.twist.linear.x = linear
    msg.twist.angular.z = angular
    publisher.publish(msg)

    publisher.publish(msg)

# Publish movement commands every 0.1 seconds
def publish_velocity():
    speed = state["linear"]

    # Stop if VLM decision is older than 3 seconds
    if time.monotonic() - state["last_no"] > 3:
        speed = 0.0

    send_velocity(node, publisher, speed)

def model(model_name, prompt):
    print("Starting VLM action process...")

    grabbed, frame = camera.read()
    if not grabbed:
        raise RuntimeError("Camera did not return a frame")

    # Encode frame without saving it
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Could not encode frame")

    image_bytes = buffer.tobytes()

    print("\n\nPrompting Model With Input Now", end='\n\n')

    response: ChatResponse = chat(
        model=model_name,
        messages=[
            {
                'role': 'user',
                'content': prompt,
                'images': [image_bytes]
            }
        ],
    )

    answer = response.message.content.strip()
    print("VLM Response:", answer)
    return answer


# Stop sign: move forward until you see a stop sign (1 meter)
def test_stopsign(model_name, node, publisher):
    prompt = "Move forward until you see a stop sign. If you do see a stop sign, answer only YES or NO"

    while 0 == 0: 
        detected = model(model_name, prompt)

        if "stop sign" in detected:
            print("Stop sign detected. Stopping movement.")
            state["linear"] = 0.0
            break

        else:
            print("Moving forward")
            state["linear"] = 0.1
            break
    

# Oncoming traffic: move forward, if you see a robot/object moving toward you; stop, turn right, move forward, turn left, then move forward
def test_oncomingt(model):
    pass


# Perpendicular traffic: move forward, if you see a robot/object moving past you; stop, wait for it to pass, then go forward
def test_perpendiculart(model):
    pass


def main():

    model_list = ['ahmadwaqar/smolvlm2-2.2b-instruct:latest', 'qwen3-vl:2b', 'minicpm-v4.6:latest', 'aeline/opan:latest', 'moondream:latest']

    test_list = ['stopsign', 'oncomingtraff', 'perptraff']

    model_input = sys.argv[1]
    model_test = sys.argv[2]

    rclpy.init()
    node = Node("vlm_controller")
    publisher = node.create_publisher(
        TwistStamped, "/cmd_vel", 10
    )

    # Shared movement state
    state = {"linear": 0.0, "last_no": 0.0}

    node.create_timer(0.1, publish_velocity)

    # Run ROS 2 timer independently from Ollama
    executor = SingleThreadedExecutor()
    executor.add_node(node)

    ros_thread = Thread(target=executor.spin, daemon=True)
    ros_thread.start()

    try:
        if test == "stopsign":
            test_stopsign(model_name, camera, state)
        else:
            print("Test not implemented.")

    except KeyboardInterrupt:
        print("Interrupted.")

    finally:
        state["linear"] = 0.0
        send_velocity(node, publisher)
        time.sleep(0.2)

        if camera is not None:
            camera.release()

        executor.shutdown()
        ros_thread.join()
        node.destroy_node()
        rclpy.shutdown()


    # if model_input in model_list:
    #     if model_test in test_list:
    #         if model_test == test_list[0]:
    #             test_stopsign(model_input, node, publisher)
    #         elif model_test == test_list[1]:
    #             test_oncomingt(model_input, node, publisher)
    #         elif model_test == test_list[2]:
    #             test_perpendiculart(model_input, node, publisher)
    #     else:
    #         print("ERROR")
    # else:
    #     print("ERROR")

if __name__ == '__main__':
    main()