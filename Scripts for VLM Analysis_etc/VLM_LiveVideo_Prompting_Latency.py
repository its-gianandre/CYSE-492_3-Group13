# Gian Fernandez 9/28/26
# (Script is based off Shanti's previous script to run Moondream)

#modified 9-29-26 by shanti

#modified 10-5 to 10-6/26 by shanti for latency recording

#needs pip install ollama 
#and pip install webcam

#also need to pull the model
#example: ollama pull moondream:latest

#The code below follows the basic usage from: https://github.com/ollama/ollama-python

from ollama import chat
from ollama import ChatResponse
from webcam import Webcam #(code related to this module is from here: https://pypi.org/project/webcam/)

import cv2

#all time related code comes from here: https://www.geeksforgeeks.org/python/python-time-module/
import time

#all csv related code comes from here: https://www.geeksforgeeks.org/python/writing-csv-files-in-python/
import csv

#all sys related code comes from here: https://www.geeksforgeeks.org/python/command-line-arguments-in-python/
import sys

# Open and read the camera
camera = Webcam(src=0, w=1080, h=1920, as_bgr=True) #logitech c920 is 1920x1080p resolution

data_to_csv =[]
num_prompt = 0

check_pass = False

try: 
	args = "".join(sys.argv[-1])
	args_split = args.split('.')
	#need to check if argument doesn't end with .csv
	if((len(sys.argv[0:]) < 3) or (args_split[-1] != 'csv')):
		print("\n\nERROR: Argument should include the model name and the .csv name\nEx: python3 VLM_LiveVideo_Prompting.py moondream:latest example.csv", end='\n\n')

	else:
		print('\n\nStarting VLM prompt process, please start the power analysis script at the same time', end='\n\n')

		check_pass = True

		model_name = sys.argv[1]

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

			row_data = None

			t_init = time.time()
			response: ChatResponse = chat(
			# Change Model as needed
				model = model_name,
				messages =[ 
					{
						'role' : 'user',
						'content' : 'Describe what is happening in the video feed in one 			sentence.',
				"images": [image_bytes],
				},
					],
				)

			t_final = time.time()
			print(f'\n\nVLMs Response: {response.message.content}', end = '\n\n')

			t_latency = t_final - t_init

			num_prompt += 1

			row_data = {"Prompt #": num_prompt, "Initial Time": t_init, "Final Time": t_final, "Latency Time": t_latency}
			data_to_csv.append(row_data)
	

except KeyboardInterrupt:
	csv_fname = "".join(sys.argv[-1])
	print(f"\n\nScript Stopped by user. Saving Latency Data to file: {csv_fname}")
	
	with open(csv_fname, 'w', newline = '') as csvfile:
		fnames = ['Prompt #', 'Initial Time', 'Final Time', "Latency Time"]
		writer = csv.DictWriter(csvfile, fieldnames=fnames)
		writer.writeheader()
		writer.writerows(data_to_csv)

	print(f"\nCompleted - Latency Data saved to file: {csv_fname}", end = '\n\n')

finally:
	camera.release()

if(check_pass is True):
	print('\n\n End of VLM Prompt Process, please check the VLM timing reponense results')
	print('\n End of VLM Prompt Process, please check the power analysis results', end= '\n\n')
