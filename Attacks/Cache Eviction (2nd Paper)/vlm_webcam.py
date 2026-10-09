# bella m 10/5/2026
# also need to pull the model
# example: ollama pull moondream:latest
# to run in bash:  python3 vlm_webcam.py
# The code below follows the basic use of: https://github.com/ollama/ollama-python

from ollama import chat
from ollama import ChatResponse
from webcam import Webcam #(code related from https://pypi.org/project/webcam/)

import cv2
import csv
import os
import time
from datetime import datetime

# controllable via environment variables 
EVICT_MODEL_EVERY_FRAME = os.environ.get("VLM_EVICT", "0") == "1"
LABEL = os.environ.get("VLM_LABEL", "run")
DURATION = float(os.environ.get("VLM_DURATION", "0"))  # 0 = run forever, to stop crtl + c
MODEL = os.environ.get("VLM_MODEL", "minicpm-v4.6:latest")  # which Ollama model to test

# profile video of live feed in avi format
VIDEO_SOURCE = os.environ.get("VLM_VIDEO_SOURCE", "")  # empty string = use live camera (original behavior)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
latency_file = f"latency_{LABEL}_{timestamp}.csv"

print('\n\n Starting VLM prompt process, please start the power analysis script at the same time', end='\n\n')
if EVICT_MODEL_EVERY_FRAME:
	print("Model eviction is ON -- model will reload from scratch every frame (slower, on purpose).\n")
if DURATION > 0:
	print(f"Will run for {DURATION:.0f} seconds, then stop automatically.\n")
print(f"Model: {MODEL}")
if VIDEO_SOURCE:
	print(f"Input source: recorded video ({VIDEO_SOURCE}) -- same content every run")
else:
	print("Input source: live camera")
print(f"Latency log: {latency_file}\n")

# Open either the recorded video file or the live camera. cv2.VideoCapture handles both cases
using_video_file = bool(VIDEO_SOURCE)
if using_video_file:
	camera = cv2.VideoCapture(VIDEO_SOURCE)
	if not camera.isOpened():
		raise SystemExit(f"Could not open video file: {VIDEO_SOURCE}")
else:
	# src=0 maps to /dev/video0. w/h here are swapped relative to the C920's native
	# 1920x1080 -- if the image looks squished/cropped, try swapping them
	camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution

start_time = time.time()
frame_no = 0

try:
	with open(latency_file, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["frame", "time", "latency_s", "response_preview"])

		while True:
			# If a duration was set (via run_attack.sh) stop automatically once it elapses 
			# continues forever with value 0 until stopped 
			if DURATION > 0 and (time.time() - start_time) >= DURATION:
				print(f"\n{DURATION:.0f}-second run complete.")
				break

			# Pull the next frame
			grabbed, frame = camera.read()

			if not grabbed:
				if using_video_file:
					# Reached the end of the recorded video before DURATION elapsed --
					# loop back to the start rather than crashing
					# every run started reading from frame 0
					camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
					grabbed, frame = camera.read()
					if not grabbed:
						raise RuntimeError("Video file appears empty or unreadable")
				else:
					# Camera disconnected, busy, or otherwise failed to return a frame --
					# fail loudly rather than silently sending a stale/empty frame to the model.
					raise RuntimeError("Camera did not return a frame")

			# Encode the raw frame as JPEG bytes in memory (Ollama works better with JPEG)
			success, buffer = cv2.imencode(".jpg", frame)
			if not success:
				raise RuntimeError("Could not encode frame")

			image_bytes = buffer.tobytes()

			print("\n\nPrompting Model With Input Now", end='\n\n')

			# Record the time right before sending the request
			request_start = time.time()

			# Send the frame + prompt to the model and wait for a full response
			response: ChatResponse = chat(
			# change model if needed
	        	model = MODEL,
	        	messages =[ 
	            	{
	                	'role' : 'user',
	                	'content' : 'Describe what is happening in the video feed in one sentence.',
				"images": [image_bytes],  # the actual image data sent to the VLM
	           	 },
	        		],
			# "5m" keeps the model loaded in GPU memory between calls
			# only the FIRST request pays a load cost
			# "0" unloads it immediately after every single response, forcing every request to reload from scratch
			keep_alive = 0 if EVICT_MODEL_EVERY_FRAME else "5m",
	    		)

			request_end = time.time()
			latency = request_end - request_start
			frame_no += 1

			print(f'\n\nVLMs Response: {response.message.content}', end = '\n\n')
			print(f'Response latency: {latency:.2f} seconds', end='\n\n')

			# Write this frame's latency to the CSV immediately
			writer.writerow([frame_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			                  round(latency, 3), response.message.content.replace("\n", " ")[:150]])
			f.flush()
			#time.sleep(2)   # optional pause between frames -- currently disabled, so this loops as fast as the camera + model allow

except KeyboardInterrupt:
	print("\nStopped by user.")

finally:
	# Always release the camera/video device on exit (even after Ctrl+C or an error
	# above), so it isn't left locked for the next run.
	camera.release()

print('\n\n End of VLM Prompt Process, please check the power analysis results', end= '\n\n')
print(f'Latency data saved to: {latency_file}')
