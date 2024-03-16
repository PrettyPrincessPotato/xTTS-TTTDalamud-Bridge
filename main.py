'''
TODO:
    Reorganize files to modulate and organize the project
    Add a way to pause the audio
'''

# IMPORTS
import json
import requests
import roman
import io
import sys
import os
import threading
import queue
import random
import select
import time
import warnings
import logging
import re
import os
import csv
import my_app.dataManager as dM
import soundfile as sf
import numpy as np
from pynput import mouse
from pynput import keyboard
from inflect import engine
from requests import Request, Session
from websocket import create_connection
from my_app.audioPlayer import play_audio

# Create an inflect engine, which is used to pluralize words.
inflect_engine = engine()

# Set up the JSON paths
json_paths = dM.setup_json_paths()

# Use the paths from the dictionary
DICT_JSON_PATH = json_paths['DICT_JSON_PATH']
FEMALE_VOICES_JSON_PATH = json_paths['FEMALE_VOICES_JSON_PATH']
FUNNY_NAMES_JSON_PATH = json_paths['FUNNY_NAMES_JSON_PATH']
IMPORTANT_VOICES_JSON_PATH = json_paths['IMPORTANT_VOICES_JSON_PATH']
MALE_VOICES_JSON_PATH = json_paths['MALE_VOICES_JSON_PATH']
SYMBOLS_AND_EMOTES_JSON_PATH = json_paths['SYMBOLS_AND_EMOTES_JSON_PATH']


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

# Stores the session as a variable so credentials are not needed to be entered every time.
s = Session()

# Defines the path to the CSV file which is the TTS server URL
csv_file_path = './secretKeys/URL.csv'

# Loads the private CSV so that the TTS server URL doesn't get leaked
with open(csv_file_path, mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    # Since the CSV contains only one line with the URL, we can use next() to read it
    url = next(csv_reader)[0]  # This assumes the URL is in the first column

# Should the script be running?
runScript = threading.Event()

# Create two queues, one for the requests and one for the audio data
request_queue = None
audio_queue = queue.Queue()

# Set the request_queue to the queue passed in, or create a new queue if none is passed in.
# This function is used to set the request_queue from the test script
def set_request_queue(q):
    global request_queue
    request_queue = q

if request_queue is None:
    request_queue = queue.Queue()



############################################
# ASSIGN THE VOICE TO WHOMEVER IS TALKING  #
############################################
def get_voice(speaker, gender=None, source=None):
    # Read each default voice and every importantVoice and assign them variables.
    with open(MALE_VOICES_JSON_PATH, 'r') as f:
        maleVoices = json.load(f)
    with open(FEMALE_VOICES_JSON_PATH, 'r') as f:
        femaleVoices = json.load(f)
    with open(IMPORTANT_VOICES_JSON_PATH, 'r') as f:
        importantVoices = json.load(f)
    # Check if this voice is assigned already
    if speaker in importantVoices:
        return importantVoices[speaker]
    # Not registered? Make a new one.
    if gender == "Male":
        male_voices = list(maleVoices.values())
        voice = random.choice(male_voices)
    elif gender == "Female":
        female_voices = list(femaleVoices.values())
        voice = random.choice(female_voices)
    else:
        # Get a list of all voices
        all_voices = list(femaleVoices.values()) + list(maleVoices.values())
        # Return a random voice
        voice = random.choice(all_voices)

    # Check if the source is 'Chat' and if the gender is not defined
    if source == 'Chat' and gender == 'None':
        return voice  # If both conditions are met, return the voice without saving it
    
    if speaker == '' or speaker == '???':
        return voice # If the speaker is empty, return the voice without saving it

    # Save the assigned voice to importantVoices json
    importantVoices[speaker] = voice
    with open(IMPORTANT_VOICES_JSON_PATH, 'w') as f:
        json.dump(importantVoices, f, indent=4)
    
    return voice

# Function to symbols and emoticons
def replace_symbols_and_emoticons(text):
    # Load the symbols and emoticons from the JSON file
    with open(SYMBOLS_AND_EMOTES_JSON_PATH, 'r') as f:
        symbolsAndEmotesJson = json.load(f)

    # Replace each symbol or emoticon in the text
    for symbol, replacement in symbolsAndEmotesJson.items():
        text = text.replace(symbol, replacement)

    return text

def convert_roman_numerals_to_arabic(words_and_punctuation):
    processed_words = []
    for word in words_and_punctuation:
        logger.debug(f"DEBUG: in convert_roman_numerals_to_arabic - Word being checked: {word}")
        if word.lower() == 'i':
            # If the word is 'I' or 'i', keep it as it is
            processed_words.append(word)
        else:
            try:
                # Try to convert the word from a Roman numeral to an Arabic numeral
                arabic_numeral = roman.fromRoman(word.upper())
                logger.debug(f"DEBUG: in convert_roman_numerals_to_arabic - Converted Roman numeral to Arabic numeral: {arabic_numeral}")
                processed_words.append(str(arabic_numeral))
            except:
                # If the word is not a valid Roman numeral, keep it as it is
                logger.debug(f"DEBUG: in convert_roman_numerals_to_arabic - {word} is not a valid Roman numeral")
                processed_words.append(word)
    return processed_words

############################################
# PROCESS THE REQUESTS AND SEND TO SERVER  #
############################################
def process_request():
    while not runScript.is_set():            
        try:
            # Get the next request from the request_queue
            jsonFile = request_queue.get(timeout=1) # Get the next request from the queue, but timeout after 1 second
            logger.debug("DEBUG: Got item from queue")
            logger.debug("DEBUG: jsonFile: ", jsonFile)
        except queue.Empty:  # If the queue is empty
            continue  # Continue to the next iteration of the loop, so it can check if the script should be running again.

        # Get the voice of the speaker.
        logger.debug("DEBUG: Getting voice")
        voice = get_voice(jsonFile["Speaker"], jsonFile["Voice"].get("Name"), jsonFile.get("Source"))
        logger.debug("DEBUG: Got voice: ", voice)

        # Get the payload from the request
        payload = jsonFile["Payload"]
        logger.debug("DEBUG: Payload assigned from jsonFile. Payload:")
        logger.debug(payload)
        
        # replace symbols and emotes
        payload = replace_symbols_and_emoticons(payload)
        logger.debug("DEBUG: Replaced symbols and emoticons to be phonetic. Payload: ")
        logger.debug(payload)

        # Split the payload into words and punctuation
        words_and_punctuation = re.findall(r"[\w'-]+|[.,!?;:-]", payload)
        logger.debug("DEBUG: Split payload into words and punctuation: ")
        logger.debug(words_and_punctuation)

        # Replace roman numerals to arabic
        words_and_punctuation = convert_roman_numerals_to_arabic(words_and_punctuation)
        logger.debug("DEBUG: Converted Roman numerals to Arabic numerals. words_and_punctuation:")
        logger.debug(words_and_punctuation)

        # Create a list to store the corrected words and punctuation
        corrected_words_and_punctuation = []
        logger.debug("DEBUG: Created list to store corrected words and punctuation")
        logger.debug(corrected_words_and_punctuation)

        # Load the pronunciation dictionary
        with open(DICT_JSON_PATH, 'r') as f:
            pronunciation_dict = json.load(f)
            logger.debug("DEBUG: Loaded pronunciation dictionary")
            logger.debug(pronunciation_dict)
                
        # Load the funny names dictionary
        with open(FUNNY_NAMES_JSON_PATH, 'r') as f:
            funny_names_dict = json.load(f)
            logger.debug("DEBUG: Loaded funny names dictionary")
            logger.debug(funny_names_dict)

        # Iterate through the words and punctuation
        for word_or_punctuation in words_and_punctuation:
            logger.debug("DEBUG: Word being checked: ")
            logger.debug(word_or_punctuation)
            corrected = False  # Flag to check if the word has been corrected
            # If the word is in the funny names dictionary, occasionally replace it
            logger.debug("DEBUG: Corrected? - Before random chance for funny_names_dict:")
            logger.debug(corrected)
            if word_or_punctuation.lower() in funny_names_dict and random.random() < 0.01:  # 1% chance
                logger.debug("DEBUG: Congrats! You got the 1 percent chance for funny_names_dict!")
                logger.debug("DEBUG: Any more debugging is irrelivant for now, as the word being replaced is so hilariously different you would know if it worked.")
                logger.debug("DEBUG: this is an issue for later tater.")
                # Randomly select a replacement from the list
                corrected_word_or_punctuation = random.choice(funny_names_dict[word_or_punctuation.lower()])
                corrected = True  # Update the flag
            elif word_or_punctuation.lower().endswith('s') and word_or_punctuation.lower()[:-1] in funny_names_dict and random.random() < 0.01:  # 1% chance:
                logger.debug("DEBUG: Congrats! You got the 1 percent chance for funny_names_dict! (plural)")
                logger.debug("DEBUG: Any more debugging is irrelivant for now, as the word being replaced is so hilariously different you would know if it worked.")
                logger.debug("DEBUG: this is an issue for later tater.")
                # Randomly select a replacement from the list and pluralize it
                corrected_word_or_punctuation = inflect_engine.plural(random.choice(funny_names_dict[word_or_punctuation.lower()[:-1]]))
                corrected = True  # Update the flag

            if not corrected and word_or_punctuation.lower() in pronunciation_dict:
                corrected_word_or_punctuation = pronunciation_dict[word_or_punctuation.lower()]
                corrected = True  # Update the flag
            # Otherwise, keep the word or punctuation as it is
            if not corrected:
                corrected_word_or_punctuation = word_or_punctuation
            # Add the corrected word or punctuation to the list
            corrected_words_and_punctuation.append(corrected_word_or_punctuation)
        # Join the corrected words and punctuation back together
        corrected_payload = " ".join(corrected_words_and_punctuation)
        # Remove spaces before punctuation
        corrected_payload = corrected_payload.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?").replace(" ;", ";").replace(" :", ":").replace(" -", "-")  
        logger.debug("DEBUG: Corrected payload: ")
        logger.debug(corrected_payload)

        # Defines data, the json input required to get audio back
        logger.debug("DEBUG: Creating data dict")
        data_dict = {"text": corrected_payload, "speaker_wav": voice, "language": "en"}
        logger.debug("DEBUG: data_dict input: ", data_dict)
        data = json.dumps(data_dict)

        # defines req, a POST request using URL and Data to send that information.
        logger.debug("DEBUG: Creating request")
        req = Request('POST', url, data=data)
        # defines prepped, which requires the request to be prepared for some weird fuckin reason
        prepped = req.prepare()

        # defines resp, which is when we send the prepped request with Session()
        max_retries = 1
        for i in range(max_retries):
            try:
                resp = s.send(prepped)
                if resp.status_code != 200:  # Check if the status code is not 200
                    logger.error(f"Error: Received status code {resp.status_code} from TTS server. Response content:")
                    logger.error(resp.content.decode())  # Print the response content
                    raise requests.exceptions.HTTPError(f"Received status code {resp.status_code}")  # Raise an exception
                break # If the request is successful, break out of the loop
            except requests.exceptions.RequestException as e:
                if i < max_retries - 1: 
                    logger.error(f"Request failed with error {e}. Retrying...")
                    continue  # If we haven't reached the max retries, go to the next iteration
                else:
                    logger.error(f"Request failed after {max_retries} attempts. Error: {e}")
                    continue  # If we've reached the max retries, continue to the next iteration instead of returning

        # Assuming audio_data is your byte data
        audio_data = resp.content

        # Try to read the response as an audio file
        try:
            data, samplerate = sf.read(io.BytesIO(audio_data))
        except RuntimeError:
            logger.error("Error: Unable to read response from TTS server as an audio file.")
            continue  # Skip the rest of this iteration and go back to the start of the loop

        audio_queue.put((audio_data, jsonFile))  # Put the audio data in the audio queue, this should be a .wav file.

# Start a worker thread
worker = threading.Thread(target=process_request)
worker.start()

# Clear the queue
def clear_queue(q):
    while not q.empty():
        try:
            q.get_nowait()  # Non-blocking get
        except queue.Empty:
            break  # The queue is empty
        q.task_done()  # Indicate that the item has been processed

# Start the play_audio function in one thread
logger.debug("Starting play_audio thread")
play_audio_thread = threading.Thread(target=play_audio, args=(runScript, audio_queue))
logger.debug(f"play_audio_thread: {play_audio_thread}")
play_audio_thread.start()
logger.debug("Started play_audio thread")

############################################
# CONNECT TO THE WEBSOCKET AND GET MESSAGES#
############################################
def main():
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
                        request_queue.put(jsonFile)
            except Exception as e:
                logger.error(f"Failed to connect to the websocket: {e}")
                time.sleep(1)  # Wait for a second before retrying


# Define this function as the debug thread.
def debug():    
    while not runScript.is_set():
        command = input("Enter a command: ")

        if command == "debug on":
            print("Debug mode on")
            logger.setLevel(logging.DEBUG)

        elif command == "debug off":
            print("Debug mode off")
            logger.setLevel(logging.INFO)

        elif command == "exit":
            print("Shutting down...")
            runScript.set()
            clear_queue(request_queue)
            clear_queue(audio_queue)
            
            for thread in threading.enumerate():
                logger.debug(thread.name)
            logger.debug("Attempting to join worker thread")
            worker.join()
            logger.debug("Joined worker thread")
            main_thread.join()
            logger.debug("Joined main thread")
            play_audio_thread.join()
            logger.debug("Joined play_audio thread")
            logger.debug("Joined debug thread")
            break

        elif command == "help":
            print(f'Logger is set to {logger.getEffectiveLevel()} mode.')
            print("===== debug on =====")
            print("Turns debug mode on.")
            print("===== debug off =====")
            print("Turns debug mode off.")
            print("===== exit =====")
            print("exits the program.")

# Warning suppressions
warnings.filterwarnings("ignore", "process_audio is not defined")
warnings.filterwarnings("ignore", "samplerate is not defined")

# Start the main function in one thread
main_thread = threading.Thread(target=main)
main_thread.start()

# Start the debug function in another thread
debug_thread = threading.Thread(target=debug)
debug_thread.start()

# Wait for all tasks in the queues to be done
request_queue.join()
audio_queue.join()
