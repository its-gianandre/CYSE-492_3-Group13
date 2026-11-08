from ollama import chat
from webcam import Webcam
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node

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

    print(f'\n\nVLMs Response: {response.message.content}')
    return str(response.message.content)


# Stop sign: move forward until you see a stop sign (1 meter)
def test_stopsign(model_name, node, publisher):
    prompt = "Move forward until you see a stop sign. If you do see a stop sign, answer only YES or NO"

    try:
        while 0 == 0: 
            send_velocity(node, publisher) # Stop during inference

            detected = model(model_name, prompt)

            if detected == "YES":
                print("Stop sign detected. Stopping movement.")
                break

            elif detected == "NO":
                print("No stop sign detected. Moving forward")
                time.sleep(0.1)

    except KeyboardInterrupt:
        camera.release()
        sys.exit(0)

    finally:
        send_velocity(node, publisher, linear=0.0)
        print("Stopping movement.")
        camera.release()

# Oncoming traffic: move forward, if you see a robot/object moving toward you; stop, turn right, move forward, turn left, then move forward
def test_oncomingt(model):
    pass


# Perpendicular traffic: move forward, if you see a robot/object moving past you; stop, wait for it to pass, then go forward
def test_perpendiculart(model):
    pass


def main():

    rclpy.init()
    node = Node("vlm_controller")
    publisher = node.create_publisher(
        TwistStamped, "/cmd_vel", 10
    )

test_stopsign(model_name, node, publisher)

    model_list = ['ahmadwaqar/smolvlm2-2.2b-instruct:latest', 'qwen3-vl:2b', 'minicpm-v4.6:latest', 'aeline/opan:latest', 'moondream:latest']

    test_list = ['stopsign', 'oncomingtraff', 'perptraff']

    model_input = sys.argv[1]
    model_test = sys.argv[2]

    if model_input in model_list:
        if model_test in test_list:
            if model_test == test_list[0]:
                test_stopsign(model=model_input)
            elif model_test == test_list[1]:
                test_oncomingt(model=model_input)
            elif model_test == test_list[2]:
                test_perpendiculart(model=model_input)
        else:
            print("ERROR")
    else:
        print("ERROR")

if __name__ == '__main__':
    main()