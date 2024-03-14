import json
import queue
import threading
import os
import logging

os.environ['TEST_MODE'] = 'true'

# Import your main script
import main  # Replace this with the name of your script

# Override the setup_json_paths function to set up paths for the test environment
def setup_json_paths_for_test():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    main.DICT_JSON_PATH = os.path.join(test_dir, 'data', 'dict.json')
    main.FEMALE_VOICES_JSON_PATH = os.path.join(test_dir, 'data', 'femaleVoices.json')
    main.FUNNY_NAMES_JSON_PATH = os.path.join(test_dir, 'data', 'funnyNames.json')
    main.IMPORTANT_VOICES_JSON_PATH = os.path.join(test_dir, 'data', 'importantVoices.json')
    main.MALE_VOICES_JSON_PATH = os.path.join(test_dir, 'data', 'maleVoices.json')
    main.SYMBOLS_AND_EMOTES_JSON_PATH = os.path.join(test_dir, 'data', 'symbolsAndEmotes.json')

# Call the function to set up paths for the test environment
setup_json_paths_for_test()

# This is the request you want to send to your script
fake_request = {
    'Speaker': 'Potato Princess',
    'Type': 'Say',
    'Payload': 'this is a test of the TTS system. i am not Alphinaud. I am enjoying this great game of Final Fantasy xiv. I am also a very gay tater.',
    'Voice': {
        'Id': -1,
        'Name': 'Female',
        'Rate': 0,
        'Volume': 0,
        'VoiceName': None,
        'EnabledBackend': 1
    },
    'Source': 'Chat'
}

# Set up the logger
logging.basicConfig(filename='project.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger('test')  # Use a different logger name

# Now you can use logger.debug(), logger.info(), etc. in test.py
logger.debug("This is a debug message from test.py")

# This is the queue you want to put the request into
request_queue = queue.Queue()

# Set the request_queue of your main script to the request_queue of your test script
main.set_request_queue(request_queue)

# Put the fake request into the queue
request_queue.put(fake_request)

# This is the threading event that controls whether your script is running
runScript = threading.Event()

# Start your script
main.main()  # Assuming your main function is named "main"