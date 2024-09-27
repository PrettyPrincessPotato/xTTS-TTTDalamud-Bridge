import os
import time
import logging
import json
import select
import my_app.queueManager as qM
from websocket import create_connection

# Create a logger
logger = logging.getLogger(__name__)

############################################
# CONNECT TO THE WEBSOCKET AND GET MESSAGES#
############################################
def websocket_handler(runScript):
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