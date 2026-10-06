# also need to pull the model
# example: ollama pull moondream:latest

# The code below follows the basic usage from: https://github.com/ollama/ollama-python

from ollama import chat
from ollama import ChatResponse
from webcam import Webcam #(code related to this module is from here: https://pypi.org/project/webcam/)

import cv2
import time

# Set this to True to force Ollama to UNLOAD the model from GPU memory after every
# single frame, so the next frame has to pay a full reload cost instead of reusing an
# already-loaded model 
# run once with this False (normal) and once with this True (degraded), and compare
# the two resulting power/timing logs from your jtop script
EVICT_MODEL_EVERY_FRAME = False  # change this line to True for degradation

print('\n\n Starting VLM prompt process, please start the power analysis script at the same time', end='\n\n')
if EVICT_MODEL_EVERY_FRAME:
	print("Model eviction is ON -- model will reload from scratch every frame (slower, on purpose).\n")

# Open and read the camera. src=0 maps to /dev/video0. w/h here are swapped relative to
# the C920's native 1920x1080 -- if the image looks squished/cropped, try swapping them.
camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution


try: 

	while True:
		grabbed, frame = camera.read() # Pull the newest available frame from the camera

		if not grabbed:
			# Camera disconnected, busy, or failed to return a frame 
			raise RuntimeError("Camera did not return a frame")

		success, buffer = cv2.imencode(".jpg", frame) #encode the raw frame as JPEG bytes in memory
		if not success:
			raise RuntimeError("Could not encode frame")

		image_bytes = buffer.tobytes()
		
		print("\n\nPrompting Model With Input Now", end='\n\n')
        
		#send the frame + prompt to the model and wait for a full response.
		response: ChatResponse = chat(
        	model = 'minicpm-v4.6:latest', #change model here if using other model 
        	messages =[ 
            	{
                	'role' : 'user',
                	'content' : 'Describe what is happening in the video feed in one sentence.',
			"images": [image_bytes],  # the actual image data sent to the VLM
           	 },
        		],
		# "5m" (default) keeps the model loaded in GPU memory between calls
		# "0" unloads it after every single response, forcing every request to reload from scratch 
		keep_alive = 0 if EVICT_MODEL_EVERY_FRAME else "5m",
    		)
		print(f'\n\nVLMs Response: {response.message.content}', end = '\n\n') 
		#time.sleep(2)   # optional pause between frames, currently disabled, so this loops as fast as the camera + model allow

except KeyboardInterrupt:
	print("\nStopped by user.")

finally:
	camera.release() #release the camera device on exit

print('\n\n End of VLM Prompt Process, please check the power analysis results', end= '\n\n')
