# Gian Fernandez 9/28/26
# (Script is based off Shanti's previous script to run Moondream)

#modified 9-29-26 by shanti

#needs pip install ollama 
#and pip install webcam

#also need to pull the model
#example: ollama pull moondream:latest

#The code below follows the basic usage from: https://github.com/ollama/ollama-python

from ollama import chat
from ollama import ChatResponse
from webcam import Webcam #(code related to this module is from here: https://pypi.org/project/webcam/)

import cv2
import time

print('\n\n Starting VLM prompt process, please start the power analysis script at the same time', end='\n\n')

# Open and read the camera
camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution


try: 

	while True:
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
		# Change Model as needed
        	model = 'moondream:latest',
        	messages =[ 
            	{
                	'role' : 'user',
                	'content' : 'Describe what is happening in the video feed in one 			sentence.',
			"images": [image_bytes],
           	 },
        		],
    		)
		print(f'\n\nVLMs Response: {response.message.content}', end = '\n\n') 
		#time.sleep(2)

except KeyboardInterrupt:
	print("\nStopped by user.")

finally:
	camera.release()

print('\n\n End of VLM Prompt Process, please check the power analysis results', end= '\n\n')
