#### THIS IS THE CLASS REWORK OF THE PROJECT.PY FILE ####
#### IF YOU ARE TRYING TO RUN THIS, PLEASE USE MASTER BRANCH ####

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
import threading
import time
import queue
import random
from websocket import create_connection
import select
import time
import warnings
import logging
import re
import pyautogui
from pynput import mouse
from pynput import keyboard

debug = True  # Initialize debug

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

# These will be set to True when a mouse or keyboard event occurs, respectively
mouse_event_occurred = False
keyboard_event_occurred = False

# Function to clear a queue
def clear_queue(q):
    while not q.empty():
        try:
            q.get_nowait()  # Non-blocking get
        except queue.Empty:
            break  # The queue is empty
        q.task_done()  # Indicate that the item has been processed

############################################
# VOICE MANAGER CLASS                      #
############################################
class VoiceManager:
    def __init__(self):
        self.runScript = threading.Event()
        self.load_json_files()
        self.json_refresh_thread = threading.Thread(target=self.refresh_json_files)
        self.json_refresh_thread.start()

    def load_json_files(self):
        with open('maleVoices.json', 'r') as f:
            self.maleVoices = json.load(f)
        with open('femaleVoices.json', 'r') as f:
            self.femaleVoices = json.load(f)
        with open('importantVoices.json', 'r') as f:
            self.importantVoices = json.load(f)

    def refresh_json_files(self):
        while not self.runScript.is_set():
            time.sleep(60)  # Wait for 60 seconds
            self.load_json_files()

    def stop(self):
        self.runScript.set()
        self.json_refresh_thread.join()

    def get_voice(self, speaker, gender=None, source=None):
        # Check if this voice is assigned already
        if speaker in self.importantVoices:
            return self.importantVoices[speaker]
        # Not registered? Make a new one.
        if gender == "Male":
            male_voices = list(set(self.maleVoices.values()))
            voice = random.choice(male_voices)
        elif gender == "Female":
            female_voices = list(set(self.femaleVoices.values()))
            voice = random.choice(female_voices)
        else:
            # Get a list of all voices
            all_voices = list(set(self.femaleVoices.values()) | set(self.maleVoices.values()))
            # Return a random voice
            voice = random.choice(all_voices)

        # Check if the source is 'Chat' and if the gender is not defined
        if source == 'Chat' and gender == 'None':
            return voice  # If both conditions are met, return the voice without saving it
        
        if speaker == '' or speaker == '???':
            return voice # If the speaker is empty, return the voice without saving it

        # Save the assigned voice to importantVoices.json
        self.importantVoices[speaker] = voice
        with open('importantVoices.json', 'w') as f:
            json.dump(self.importantVoices, f, indent=4)
        
        return voice

############################################
# REQUEST PROCESSOR CLASS                  #
############################################
class RequestProcessor:
    def __init__(self, request_queue, voice_manager):
        self.runScript = threading.Event()
        self.request_queue = request_queue
        self.voice_manager = voice_manager
        self.worker_thread = threading.Thread(target=self.process_request)
        self.worker_thread.start()

    def process_request(self):
        while not self.runScript.is_set():
            if debug:
                print("DEBUG: Entered process_request function")
            try:
                # Get the next request from the request_queue
                jsonFile = self.request_queue.get(timeout=1) # Get the next request from the queue, but timeout after 1 second
                if debug:
                    print("DEBUG: PROCESS_REQUESTS - Got item from queue")
                    print("DEBUG: jsonFile: ", jsonFile)
            except queue.Empty:  # If the queue is empty
                continue  # Continue to the next iteration of the loop, so it can check if the script should be running again.

            # Get the voice of the speaker.
            if debug:
                print("DEBUG: Getting voice")
            voice = self.voice_manager.get_voice(jsonFile["Speaker"], jsonFile["Voice"].get("Name"), jsonFile.get("Source"))
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
                #if word_or_punctuation.lower() in funny_names_dict:  # Always replace it for testing
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
                print("DEBUG: Creating request...")
            req = Request('POST', url, data=data)
            # defines prepped, which requires the request to be prepared for some weird fuckin reason
            prepped = req.prepare()
            if debug:
                print("DEBUG: Prepped response defined...")

            # defines resp, which is when we send the prepped request with Session()
            max_retries = 1
            for i in range(max_retries):
                try:
                    if debug:
                        print("DEBUG: Attempting to send prepped reponse...")
                    resp = s.send(prepped)
                    if resp.status_code != 200:  # Check if the status code is not 200
                        print(f"Error: Received status code {resp.status_code} from TTS server. Response content:")
                        print(resp.content.decode())  # Print the response content
                        raise requests.exceptions.HTTPError(f"Received status code {resp.status_code}")  # Raise an exception
                    if debug:
                        print("DEBUG: Sent request and recieved response")
                    break # If the request is successful, break out of the loop
                except requests.exceptions.RequestException as e:
                    if i < max_retries - 1: 
                        print(f"Request failed with error {e}. Retrying...")
                        logger.error(f"Request failed with error {e}. Retrying...")
                        continue  # If we haven't reached the max retries, go to the next iteration
                    else:
                        logger.error(f"Request failed after {max_retries} attempts. Error: {e}")
                        continue  # If we've reached the max retries, continue to the next iteration instead of returning

            # Assuming audio_data is your byte data
            audio_data = resp.content
            #if debug:
                #print("DEBUG: audio_data: ", audio_data)

            # Try to read the response as an audio file
            try:
                data, samplerate = sf.read(io.BytesIO(audio_data))
                if debug:
                    print("DEBUG: Read response from TTS server as an audio file")
            except RuntimeError:
                print("Error: Unable to read response from TTS server as an audio file.")
                continue  # Skip the rest of this iteration and go back to the start of the loop
            
            # Convert the data to PCM
            pcm_data = np.int16(data * 32767)
            if debug:
                print ("DEBUG: pcm_data: ", pcm_data)

            audio_queue.put((pcm_data, samplerate, jsonFile))  # Put processed (PCM data and sample rate) into audio_queue
            if debug:
                print("DEBUG: Put item in queue")
                print("DEBUG: AudioQueue check:", audio_queue)

    def stop(self):
        self.runScript.set()
        clear_queue(self.request_queue)  # Clear the request_queue
        self.worker_thread.join()

############################################
# AUDIO PLAYER CLASS                       #
############################################
class AudioPlayer:
    def __init__(self):
        # Initialize audio queue and playback thread
        self.audio_queue = queue.Queue()
        self.runScript = threading.Event()
        if debug:
            print("DEBUG: AudioPlayer is running...")
        self.playback_thread = threading.Thread(target=self.play_audio)
        try:
            self.playback_thread.start()
            print("DEBUG: playback_thread.is_alive(): ", self.playback_thread.is_alive())
        except Exception as e:
            print(f"DEBUG: Exception in AudioPlayer __init__ method: {e}")
        if debug:
            print("DEBUG: Initializing AudioPlayer")
            print("DEBUG: AudioPlayer: runScript.is_set(): ", self.runScript.is_set())

    # Looks for a specific device name and returns the index of that device
    def get_device_index(self, device_name):
        p = pyaudio.PyAudio()
        print("DEBUG: Entering get_device_index function")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if debug:
                print("DEBUG: device name and index: ", info["name"], info["index"])
            if device_name in info["name"]:
                if debug:
                    print (f"DEBUG: Found device with name {device_name} at index {info['index']}")
                return info["index"]
        raise ValueError(f"No device with name {device_name} found")

    def play_audio(self):
        global mouse_event_occurred
        global keyboard_event_occurred
        while not self.runScript.is_set():
            if debug:
                print("DEBUG: PLAY_AUDIO: runScript.is_set(): ", self.runScript.is_set())
            try:
                if debug:
                    print("DEBUG: PLAY AUDIO - Trying to get item from queue")
                pcm_data, samplerate, jsonFile = self.audio_queue.get(timeout=1)  # Get next audio data from the queue
                if debug:
                    print("DEBUG: PLAY AUDIO - Got item from queue")
                    print("DEBUG: AudioQueue check:", self.audio_queue)
                    print("DEBUG: pcm_data, samplerate, jsonFile: ", pcm_data, samplerate, jsonFile)
            except queue.Empty:
                continue # Continue to the next iteration of the loop, so it can check if the script should be running again.

            # Write to a WAV file in memory
            if debug:
                print("DEBUG: Writing to a WAV file in memory")
            audio_file = io.BytesIO()
            write(audio_file, samplerate, pcm_data)
            audio_file.seek(0)  # reset file pointer to the beginning

            # Open the audio file
            if debug:
                print("DEBUG: Opening the audio file")
            wave_read = wave.open(audio_file, 'rb')

            # Initialize PyAudio
            if debug:
                print("DEBUG: Initializing PyAudio")
            p = pyaudio.PyAudio()

            # Get the indices of your desired output devices
            if debug:
                print("DEBUG: Getting device indices")
            speaker_output_index = self.get_device_index("Speakers (High Definition Audio")
            cable_output_index = self.get_device_index("CABLE Input (VB-Audio Virtual C")

            # Open a stream for the speakers
            if debug:
                print("DEBUG: Opening a stream for the speakers")
            speaker_stream = p.open(format=p.get_format_from_width(wave_read.getsampwidth()),
                                    channels=wave_read.getnchannels(),
                                    rate=wave_read.getframerate(),
                                    output=True,
                                    output_device_index=speaker_output_index)  # Use the index of your speakers

            # Open a stream for the virtual cable
            cable_stream = p.open(format=p.get_format_from_width(wave_read.getsampwidth()),
                                channels=wave_read.getnchannels(),
                                rate=wave_read.getframerate(),
                                output=True,
                                output_device_index=cable_output_index)  # Use the index of the virtual cable

            # Play the stream
            if debug:
                print("DEBUG: Playing the stream")
            data = wave_read.readframes(1024)
            while len(data) > 0:
                # Convert byte data to numpy array
                np_data = np.frombuffer(data, dtype=np.int16)
                # Reduce volume
                np_data = (np_data * 0.5).astype(np.int16)
                # Convert numpy array back to byte data and write to both streams
                speaker_stream.write(np_data.tobytes())
                cable_stream.write(np_data.tobytes())
                data = wave_read.readframes(1024)

            # Close the streams
            if debug:
                print("DEBUG: Closing the streams")
            speaker_stream.stop_stream()
            speaker_stream.close()
            cable_stream.stop_stream()
            cable_stream.close()

            # Terminate PyAudio
            if debug:
                print("DEBUG: Terminating PyAudio")
            p.terminate()

            # Simulate a mouse click to progress the message in FF14
            if jsonFile.get('Source') == 'AddonTalk':
                cooldownTime = 3
                if time.time() - mouse_event_occurred > cooldownTime and time.time() - keyboard_event_occurred > cooldownTime:
                    if debug:
                        print("DEBUG: clicking mouse...")
                    pyautogui.click(901, 222)  # random point in main monitor between my 2 monitors, your mileage may vary

                # Reset the flags
                mouse_event_occurred = False
                keyboard_event_occurred = False

            # Indicate that the task is done
            self.audio_queue.task_done()

    def stop(self):
        if debug:
            print("DEBUG: Stopping AudioPlayer")
        self.runScript.set()
        clear_queue(self.audio_queue)  # Clear the audio_queue
        self.playback_thread.join()

############################################
# WEBSOCKET CLIENT CLASS                   #
############################################
class WebSocketClient:
    def __init__(self):
        self.runScript = threading.Event()
        self.websocket = None
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()

    def main(self):
        global debug
        while not self.runScript.is_set():
            try:
                if debug:
                    print("Attempting to connect to the websocket...")
                self.websocket = create_connection("ws://localhost:8080/Messages")
                if debug:
                    print("Connected!")
                while not self.runScript.is_set():
                    if debug:
                        print("Waiting for message...")
                        print("DEBUG: REQUEST QUEUE:")
                        print(request_queue.qsize(), request_queue.queue)
                        print("DEBUG: AUDIO QUEUE:")
                        print(audio_queue.qsize(), audio_queue.queue)
                    ready_to_read, _, _ = select.select([self.websocket.sock], [], [], 1)
                    if ready_to_read:
                        if debug:
                            print("Got message!")
                        jsonString = self.websocket.recv()
                        jsonFile = json.loads(jsonString)
                        if debug:
                            print(f"DEBUG: Received message: {jsonFile}")
                        request_queue.put(jsonFile)
            except Exception as e:
                if debug:
                    print(f"Failed to connect to the websocket: {e}")
                time.sleep(1)  # Wait for a second before retrying   

    def stop(self):
        self.runScript.set()
        self.main_thread.join()       

############################################
# EVENT LISTENER CLASS                     #
############################################
class EventListener:
    def __init__(self):
        # Start the mouse and keyboard listeners
        listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click)
        listener.start()
        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        keyboard_listener.start()

    # Define listener callback functions
    def on_move(self, x, y):
        global mouse_event_occurred
        mouse_event_occurred = time.time()

    def on_click(self, x, y, button, pressed):
        global mouse_event_occurred
        mouse_event_occurred = time.time()

    def on_key_press(self, key):
        global keyboard_event_occurred
        keyboard_event_occurred = time.time()

############################################
# DEBUGGER CLASS                           #
############################################
class Debugger:
    def __init__(self, voice_manager, request_processor, audio_player, websocket_client):
        self.runScript = threading.Event()
        self.debug_thread = threading.Thread(target=self.debug)
        self.voice_manager = voice_manager
        self.request_processor = request_processor
        self.audio_player = audio_player
        self.websocket_client = websocket_client
        self.debug_thread.start()

    def debug(self):
        global debug # Declare debug as a global variable at the start of the function
        
        while not self.runScript.is_set():
            command = input("Enter a command: ")

            if command == "debug on":
                print("Debug mode on")
                debug = True

            elif command == "debug off":
                print("Debug mode off")
                debug = False

            elif command == "exit":
                print("Shutting down...")
                if debug:
                    print("===== Threads running: =====")
                    for thread in threading.enumerate():
                        print(thread.name)
                    print("=============================")
                if debug:
                    print("Setting runScript to false...")
                self.runScript.set() # Set the runScript event to stop the script
                if debug:
                    print("Stopping voice_manager...")
                self.voice_manager.stop()  # Stop the voice_manager thread
                if debug:
                    print("Stopping request_processor...")
                self.request_processor.stop()  # Stop the request_processor thread
                if debug:
                    print("Stopping audio_player...")
                self.audio_player.stop()  # Stop the audio_player thread
                if debug:
                    print("Stopping websocket_client...")
                self.websocket_client.stop()  # Stop the websocket_client thread
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

    def stop(self):
        self.runScript.set()
        self.debug_thread.join()

# Initialize the queues
request_queue = queue.Queue()
audio_queue = queue.Queue()

# Create instances of your classes
voice_manager = VoiceManager()
request_processor = RequestProcessor(request_queue, voice_manager)
event_listener = EventListener()  # Start listening for events before starting the audio player
audio_player = AudioPlayer()
websocket_client = WebSocketClient()
debugger = Debugger(voice_manager, request_processor, audio_player, websocket_client)

# Wait for all tasks in the queues to be done
request_queue.join()
audio_queue.join()

# Stop the threads when they're done
voice_manager.stop()
request_processor.stop()
audio_player.stop()
websocket_client.stop()
debugger.stop()

