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

# Set logging to INFO
logging.basicConfig(filename='project.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

# Something pretty to look at for my monke brain
print("Startup successful!")

# Stores the session as a variable so credentials are not needed to be entered every time.
s = Session()
# Defines URL as the TTS to audio link on Kelly's server
url = 'http://10.10.10.47:8020/tts_to_audio/'

# Should the script be running?
runScript = [True]

# Create a queue
q = queue.Queue()

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
            # Get the next request from the queue
            jsonFile = q.get(timeout=1) # Get the next request from the queue, but timeout after 1 second
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

        # Defines data, the json input required to get audio back
        if debug:
            print("DEBUG: Creating data dict")
        data_dict = {"text": jsonFile["Payload"], "speaker_wav": voice, "language": "en"}
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
                break # If the request is successful, break out of the loop
            except requests.exceptions.RequestException as e:
                if i < max_retries - 1: #
                    logger.error(f"Request failed with error {e}. Retrying...")
                    continue  # If we haven't reached the max retries, go to the next iteration
                else:
                    logger.error(f"Request failed after {max_retries} attempts. Error: {e}")
                    return  # If we've reached the max retries, return from the function

        # Assuming audio_data is your byte data
        audio_data = resp.content
        pcm_data, samplerate = process_audio(io.BytesIO(audio_data))  # Process the audio


        q.put((pcm_data, samplerate))  # Put processed (PCM data and sample rate) into queue

def play_audio():
    while True:
        pcm_data, audio_data = q.get()  # Get next audio data from the queue

        # Convert the data to PCM
        pcm_data = np.int16(data * 32767)

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
        q.task_done()


def process_request():
    while True:
        if not runScript[0]:  # Check if the script should be running
            break  # If not, break out of the loop
        try:
            # Get the next request from the queue
            jsonFile = q.get_nowait() # Get the next request from the queue, but timeout after 1 second
            if debug:
                print("DEBUG: Got item from queue")
        except queue.Empty:  # If the queue is empty
            continue  # Continue to the next iteration of the loop, so it can check if the script should be running again.


        # Get the voice of the speaker.
        if debug:
           print("DEBUG: jsonfile[Voice]")
           print(jsonFile["Voice"])
        voice = get_voice(jsonFile["Speaker"], jsonFile["Voice"].get("Name"))
        if debug:
            print("DEBUG: voice")
            print(voice)

        # Defines data, the json input required to get audio back
        data_dict = {"text": jsonFile["Payload"], "speaker_wav": voice, "language": "en"}
        data = json.dumps(data_dict)
        
        # defines req, a POST request using URL and Data to send that information.
        req = Request('POST', url, data=data)
        # defines prepped, which requires the request to be prepared for some weird fuckin reason
        prepped = req.prepare()

        # defines resp, which is when we send the prepped request with Session()
        resp = s.send(prepped)

        # Assuming audio_data is your byte data
        audio_data = resp.content 

        # Load the audio file
        data, samplerate = sf.read(io.BytesIO(audio_data))

        # Convert the data to PCM
        pcm_data = np.int16(data * 32767)

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
            if not runScript[0]:  # Check if the script should be running
                break  # If not, break out of the loop
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
        q.task_done()

# Start a worker thread
worker = threading.Thread(target=process_request)
worker.start()

def main(q):
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
                    q.put(jsonFile)
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
main_thread = threading.Thread(target=main, args=(q,))
main_thread.start()

# Start the debug function in another thread
debug_thread = threading.Thread(target=debug)
debug_thread.start()

# Wait for all tasks in the queue to be done
q.join()
