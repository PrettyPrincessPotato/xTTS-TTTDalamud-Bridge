# IMPORTS
import json
from requests import Request, Session
import requests
import pyaudio
import wave
import io
import soundfile as sf
import numpy as np
from scipy.io.wavfile import write
from websockets.sync.client import connect
import websockets
import threading
import queue
import random
import asyncio
from websocket import create_connection
import select
import time
import warnings
import logging
import string
import re

debug = False  # Initialize debug as False

# Set logging to INFO
logging.basicConfig(filename='project.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

# Something pretty to look at for my monke brain
print("Startup successful!")
logger.info("Starting script")

# Stores the session as a variable so credentials are not needed to be entered every time.
s = Session()
# Defines URL as the TTS to audio link on Kelly's server
url = 'https://voxbox.tigristech.org/tts_to_audio/'

# Should the script be running?
runScript = [True]

# Create two queues, one for the requests and one for the audio data
request_queue = queue.Queue()
audio_queue = queue.Queue()

def get_voice(speaker, gender=None):
    # Read each default voice and every importantVoice and assign them variables.
    with open('maleVoices.json', 'r') as f:
        maleVoices = json.load(f)
    with open('femaleVoices.json', 'r') as f:
        femaleVoices = json.load(f)
    with open('importantVoices.json', 'r') as f:
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

    # Save the assigned voice to importantVoices.json
    importantVoices[speaker] = voice
    with open('importantVoices.json', 'w') as f:
        json.dump(importantVoices, f, indent=4)
    
    return voice

def process_request():
    while True:
        if debug:
            print("DEBUG: Entered process_request function")
        if not runScript[0]:  # Check if the script should be running
            break  # If not, break out of the loop
        try:
            # Get the next request from the request_queue
            jsonFile = request_queue.get(timeout=1) # Get the next request from the queue, but timeout after 1 second
            if debug:
                print("DEBUG: Got item from queue")
        except queue.Empty:  # If the queue is empty
            continue  # Continue to the next iteration of the loop, so it can check if the script should be running again.

        # Get the voice of the speaker.
        if debug:
            print("DEBUG: Getting voice")
        voice = get_voice(jsonFile["Speaker"], jsonFile["Voice"].get("Name"))
        if debug:
            print("DEBUG: Got voice")

        # Get the payload from the request
        payload = jsonFile["Payload"]
        
        # Split the payload into words and punctuation
        words_and_punctuation = re.findall(r"[\w'-]+|[.,!?;]", payload)

        # Create a list to store the corrected words and punctuation
        corrected_words_and_punctuation = []

        # Load the pronunciation dictionary
        with open('dict.json', 'r') as f:
            pronunciation_dict = json.load(f)
                
        # Load the funny names dictionary
        with open('funnyNames.json', 'r') as f:
            funny_names_dict = json.load(f)

        # Iterate through the words and punctuation
        for word_or_punctuation in words_and_punctuation:
            # If the word is in the funny names dictionary, occasionally replace it
            if word_or_punctuation.lower() in funny_names_dict and random.random() < 0.01:  # 1% chance
                corrected_word_or_punctuation = funny_names_dict[word_or_punctuation.lower()]
            # If the word or punctuation is in the pronunciation dictionary, replace it
            elif word_or_punctuation.lower() in pronunciation_dict:
                corrected_word_or_punctuation = pronunciation_dict[word_or_punctuation.lower()]
            # Otherwise, keep the word or punctuation as it is
            else:
                corrected_word_or_punctuation = word_or_punctuation
            # Add the corrected word or punctuation to the list
            corrected_words_and_punctuation.append(corrected_word_or_punctuation)
        
        # Join the corrected words and punctuation back together
        corrected_payload = " ".join(corrected_words_and_punctuation)

        # Defines data, the json input required to get audio back
        if debug:
            print("DEBUG: Creating data dict")
        data_dict = {"text": corrected_payload, "speaker_wav": voice, "language": "en"}
        if debug:
            print("DEBUG: data_dict input: ", data_dict)
        data = json.dumps(data_dict)

        # defines req, a POST request using URL and Data to send that information.
        if debug:
            print("DEBUG: Creating request")
        req = Request('POST', url, data=data)
        # defines prepped, which requires the request to be prepared for some weird fuckin reason
        prepped = req.prepare()

        # defines resp, which is when we send the prepped request with Session()
        max_retries = 1
        for i in range(max_retries):
            try:
                resp = s.send(prepped)
                if resp.status_code != 200:  # Check if the status code is not 200
                    print(f"Error: Received status code {resp.status_code} from TTS server. Response content:")
                    print(resp.content.decode())  # Print the response content
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
            print("Error: Unable to read response from TTS server as an audio file.")
            continue  # Skip the rest of this iteration and go back to the start of the loop
        
        # Convert the data to PCM
        pcm_data = np.int16(data * 32767)

        audio_queue.put((pcm_data, samplerate))  # Put processed (PCM data and sample rate) into audio_queue

# Start a worker thread
worker = threading.Thread(target=process_request)
worker.start()

def play_audio():
    while True:
        pcm_data, samplerate = audio_queue.get()  # Get next audio data from the queue

        # Write to a WAV file in memory
        audio_file = io.BytesIO()
        write(audio_file, samplerate, pcm_data)
        audio_file.seek(0)  # reset file pointer to the beginning

        # Open the audio file
        wave_read = wave.open(audio_file, 'rb')

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Open a stream
        stream = p.open(format=p.get_format_from_width(wave_read.getsampwidth()),
                        channels=wave_read.getnchannels(),
                        rate=wave_read.getframerate(),
                        output=True)

        # Play the stream
        data = wave_read.readframes(1024)
        while len(data) > 0:
            # Convert byte data to numpy array
            np_data = np.frombuffer(data, dtype=np.int16)
            # Reduce volume
            np_data = (np_data * 0.5).astype(np.int16)
            # Convert numpy array back to byte data and write to stream
            stream.write(np_data.tobytes())
            data = wave_read.readframes(1024)

        # Close the stream
        stream.stop_stream()
        stream.close()

        # Terminate PyAudio
        p.terminate()

        # Indicate that the task is done
        audio_queue.task_done()

# Start the play_audio function in one thread
play_audio_thread = threading.Thread(target=play_audio)
play_audio_thread.start()


def main():
    global debug
    while runScript[0]:
        try:
            if debug:
                print("Attempting to connect to the websocket...")
            websocket = create_connection("ws://localhost:8080/Messages")
            if debug:
                print("Connected!")
            while runScript[0]:
                if debug:
                    print("Waiting for message...")
                ready_to_read, _, _ = select.select([websocket.sock], [], [], 1)
                if ready_to_read:
                    if debug:
                        print("Got message!")
                    jsonString = websocket.recv()
                    jsonFile = json.loads(jsonString)
                    request_queue.put(jsonFile)
        except Exception as e:
            if debug:
                print(f"Failed to connect to the websocket: {e}")
            time.sleep(1)  # Wait for a second before retrying


# Define this function as the debug thread.
def debug():
    global debug # Declare debug as a global variable at the start of the function
    debug = False  # Initialize debug
    
    while runScript[0]:
        command = input("Enter a command: ")

        if command == "debug on":
            print("Debug mode on")
            debug = True

        elif command == "debug off":
            print("Debug mode off")
            debug = False

        elif command == "exit":
            print("Shutting down...")
            runScript[0] = False
            if debug:
                for thread in threading.enumerate():
                    print(thread.name)
            if debug:
                print("Attempting to join worker thread")
            worker.join()
            if debug:
                print("Joined worker thread")
            main_thread.join()
            if debug:
                print("Joined main thread")
            break

        elif command == "help":
            if debug:
                print("psst, you're in debug mode. Here's a list of commands:")
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
