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
import sys
import os
import threading
import warnings
import logging
import os
import my_app.dataManager as dM
import my_app.requestProcessor as rP
import my_app.queueManager as qM
import my_app.audioPlayer as aP
import my_app.commandLine as cLI
import my_app.websocket as wS

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

# Defines url, which is a secret key that I use to contact xTTS.
url = dM.get_csv()

# Should the script be running?
runScript = threading.Event()

# Warning suppressions -- I forget why I need these...
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
play_audio_thread = threading.Thread(target=aP.play_audio2, args=(runScript, qM.audio_queue))
logger.debug(f"play_audio_thread: {play_audio_thread}")
play_audio_thread.start()
logger.debug("Started play_audio thread")

# Start the main function in one thread
websocket_thread = threading.Thread(target=wS.websocket_handler, args=(runScript, None)) # For some fucking reason this needs 2 args, None is there for literally no reason. DummyVar does nothing inside wS.websocket_handler. I don't know why. Please help me.
# Update it's a tuple-only instead of allowing events if there's only 1 arg. I don't understand but ok go off queen.
websocket_thread.start()

# Start the CLI function in another thread
commands_thread = threading.Thread(target=cLI.commands, args=(runScript, procces_request_thread, websocket_thread, play_audio_thread))
commands_thread.start()

# Wait for all tasks in the queues to be done
if qM.request_queue is not None:
    qM.request_queue.join()
qM.audio_queue.join()
