'''
This Python script is designed to test the functionality of main.py for processing audio and playing it back 
after sending it to a server, without needing the dalamudTTS requirement. The script is expected to run in the test mode, 
and it simulates sending requests in JSON format to be processed by main.py, which in turn communicates with external APIs.

The purpose of this script is to validate the ability of main.py to handle various types of requests, 
such as "Say" in this example, and to ensure that the necessary APIs can effectively convert the text into speech.

To use this script, run it with the F5 key in main.py.
(This next message is for me, personally. I'm not insulting you, dear reader. I promise. :) )
HEY SILLY, REMEMBER TO RUN THIS WITH F5 IN MAIN.PY. OTHERWISE, IT WON'T WORK.
'''
# Imports!
import queue
import threading
import os
import logging
import my_app.dataManager as dM
import my_app.queueManager as qM

os.environ['TEST_MODE'] = 'true'

# Import your main script
import my_app.websocket as ws

# Set up the JSON paths
# See dataManager.py for details.
json_paths = dM.setup_json_paths()

# Use the paths from the dictionary
# See dataManager.py for details.
DICT_JSON_PATH = json_paths['DICT_JSON_PATH']
FEMALE_VOICES_JSON_PATH = json_paths['FEMALE_VOICES_JSON_PATH']
FUNNY_NAMES_JSON_PATH = json_paths['FUNNY_NAMES_JSON_PATH']
IMPORTANT_VOICES_JSON_PATH = json_paths['IMPORTANT_VOICES_JSON_PATH']
MALE_VOICES_JSON_PATH = json_paths['MALE_VOICES_JSON_PATH']
SYMBOLS_AND_EMOTES_JSON_PATH = json_paths['SYMBOLS_AND_EMOTES_JSON_PATH']

# This is the request you want to send to your script
fake_request = {
    'Speaker': 'Potato Princess',
    'Type': 'Say',
    'Payload': 'this is a test of the TTS system. i am not Alphinaud. I am enjoying this great game of Final Fantasy xiv. I am also a very gay tater. Not Tatarus.',
    'Voice': {
        'Id': -1,
        'Name': 'Female',
        'Rate': 0,
        'Volume': 0,
        'VoiceName': None,
        'EnabledBackend': 1
    },
    'Source': 'AddonTalk'
}

# Set up the logger
logging.basicConfig(filename='project.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger('test')  # Use a different logger name

# Check if the 'TEST_MODE' environment variable is set
if 'TEST_MODE' not in os.environ:
    logger.error("The 'TEST_MODE' environment variable is not set. Please run this script using the Visual Studio Code debugger.")
    print("Error: The 'TEST_MODE' environment variable is not set. Please run this script using the Visual Studio Code debugger.")

# Now you can use logger.debug(), logger.info(), etc. in test.py
logger.debug("This is a debug message from test.py")

# This is the queue you want to put the request into

# Set the request_queue of your main script to the request_queue of your test script
qM.get_request_queue(main.runScript, qM.queue)

# Put the fake request into the queue
qM.request_queue.put(fake_request)

# This is the threading event that controls whether your script is running
runScript = threading.Event()

# Start your script
ws.websocket_handler()