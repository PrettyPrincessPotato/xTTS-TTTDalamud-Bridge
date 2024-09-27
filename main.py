'''
Originally built on python 3.10.11
Rebuilt on python 3.10.14

Note: for linux users: sudo dnf install portaudio-devel python3.10-devel
This command is required for pyaudio to work on linux
This will vary based on your distro.

TODO:
    Add a way to pause the audio
    Clean up requirements.txt
    Add a way to stop the audio
    Add a way to skip the audio
'''

# IMPORTS
import json
import sys
import os
import threading
import select
import time
import warnings
import logging
import os
import csv
import my_app.dataManager as dM # - Unneeded as of now, keeping just in case.
import my_app.requestProcessor as rP
import my_app.queueManager as qM
import my_app.audioPlayer as aP
import my_app.commandLine as CLI
from websocket import create_connection

# Create a logger
logger = logging.getLogger(__name__)

# Sets up the logger to output to the console if in test mode, or to a file if not.
# Also sets the logging level to DEBUG if in test mode, or to INFO if not.
if os.getenv('TEST_MODE') == 'true':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
else:
    logging.basicConfig(filename='project.log', level=logging.INFO, 
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')


# Something pretty to look at for my monke brain
print("Startup successful!")
logger.info("Starting script")

# Defines the path to the CSV file which is the TTS server URL
# url should look something like https://ttsapi.ligma.com/tts_to_audio
csv_file_path = './secretKeys/URL.csv'

# Loads the private CSV so that the TTS server URL doesn't get leaked
with open(csv_file_path, mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    # Since the CSV contains only one line with the URL, we can use next() to read it
    url = next(csv_reader)[0]  # This assumes the URL is in the first column

# Should the script be running?
runScript = threading.Event()

############################################
# CONNECT TO THE WEBSOCKET AND GET MESSAGES#
############################################
def websocket_handler():
    if os.getenv('TEST_MODE') != 'true':  # Check if the script is not running in test mode
        while not runScript.is_set():
            try:
                logger.debug("Attempting to connect to the websocket...")
                websocket = create_connection("ws://localhost:8080/Messages")
                logger.debug("Connected!")
                while not runScript.is_set():
                    logger.debug("Waiting for message...")
                    ready_to_read, _, _ = select.select([websocket.sock], [], [], 1)
                    if ready_to_read:
                        logger.debug("Got message!")
                        jsonString = websocket.recv()
                        jsonFile = json.loads(jsonString)
                        qM.request_queue.put(jsonFile)
            except Exception as e:
                logger.error(f"Failed to connect to the websocket: {e}")
                time.sleep(1)  # Wait for a second before retrying

# Warning suppressions
warnings.filterwarnings("ignore", "process_audio is not defined")
warnings.filterwarnings("ignore", "samplerate is not defined")

############################################
#                THREADS                   #
############################################

# Start the thread to process requests and make them readable for the TTS AI.
procces_request_thread = threading.Thread(target=rP.process_request, args=(runScript, qM.request_queue))
procces_request_thread.start()

# Start the play_audio function in one thread. This plays the audio.
logger.debug("Starting play_audio thread")
play_audio_thread = threading.Thread(target=aP.play_audio, args=(runScript, qM.audio_queue))
logger.debug(f"play_audio_thread: {play_audio_thread}")
play_audio_thread.start()
logger.debug("Started play_audio thread")

# Start the main function in one thread
websocket_thread = threading.Thread(target=websocket_handler)
websocket_thread.start()

# Start the CLI function in another thread
commands_thread = threading.Thread(target=CLI.commands, args=(runScript, procces_request_thread, websocket_thread, play_audio_thread))
commands_thread.start()

# Wait for all tasks in the queues to be done
if qM.request_queue is not None:
    qM.request_queue.join()
qM.audio_queue.join()
