#Shanti W. Nadimi 9/23/2026

#needs pip install ollama

#also need to pull the model
#example: ollama pull moondream:latest

#The code below follows the basic usage from: https://github.com/ollama/ollama-python

from ollama import chat
from ollama import ChatResponse

import os

#gathering file names from directory, following this: https://www.geeksforgeeks.org/python/python-list-files-in-a-directory/
path = "/home/group13/Downloads"
dir_list = os.listdir(path)


#picture files that will be analyzed by the vlm
#string array containing the various photo files that will be analyzed
pic_array = dir_list #update this string with the paths to photos

#iterating through the pic_array and prompting the vlm to analyze the photo
print('\n\n Starting VLM prompt process, please start the power analysis script at the same time', end='\n\n')

for i in pic_array:
    response: ChatResponse = chat(
        model = 'moondream:latest',
        messages =[
            {
                'role' : 'user',
                'content' : f'Please analyze the photo in the path {path + i} and tell me what it is'
            },
        ],
    )

    #printing the vlm's response
    print(f'\n\nVLMs Response: {response.message.content}', end = '\n\n')

print('\n\n End of VLM Prompt Process, please check the power analysis results', end= '\n\n')
