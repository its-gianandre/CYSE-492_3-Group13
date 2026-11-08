from ollama import chat
from ollama import ChatResponse
from webcam import Webcam
import sys

#if we use the camera here we don't need a camera node - simplier
camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution

#need to be able to use terminal args to select the model and then select the test
#i believe we had 5 VLMs on the AGX
#there are 3 tests: stop sign, oncoming traffic, perpendicular traffic

#stop sign: move forward until you see a stop sign (1 meter)

#oncoming traffic: move forward, if you see a robot/object moving toward you; stop, turn right, move forward, turn left, then move forward

#perpendicular traffic: move forward, if you see a robot/object moving past you; stop, wait for it to pass, then go forward

def test_stopsign(model):
    pass

def test_oncomingt(model):
    pass

def test_perpendiculart(model):
    pass


def main():
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