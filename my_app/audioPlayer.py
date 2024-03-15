''' TODO: create a module for the TTS to audio. 99% of what you need is in main.py
    TODO: also consider downloading the output.wav directly to mess with more. Potentially adding a better queue
          system. One that plays the data and another that loads the data? Just something to keep in mind.'''
import pyaudio
import wave
import io
import pyautogui
import time
import queue
import logging
import numpy as np
from scipy.io.wavfile import write
from pynput import mouse, keyboard

# Set up logging
logger = logging.getLogger(__name__)

# Looks for a specific device name and returns the index of that device
def get_device_index(device_name):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if device_name in info["name"]:
            return info["index"]
    raise ValueError(f"No device with name {device_name} found")

# This will be set to True when a mouse event occurs
mouse_event_occurred = False

# This will be set to True when a keyboard event occurs
keyboard_event_occurred = False

# Define the mouse and keyboard listeners
def on_move(x, y):
    global mouse_event_occurred
    mouse_event_occurred = time.time()

def on_click(x, y, button, pressed):
    global mouse_event_occurred
    mouse_event_occurred = time.time()

def on_key_press(key):
    global keyboard_event_occurred
    keyboard_event_occurred = time.time()

# Start the mouse listener
listener = mouse.Listener(on_move=on_move, on_click=on_click)
listener.start()

# Start the keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()

############################################
# PLAY THE AUDIO AND SIMULATE MOUSE CLICK  #
############################################
def play_audio(runScript, audio_queue):
    global mouse_event_occurred, keyboard_event_occurred
    logger.debug(f"play_audio called with runScript={runScript}, audio_queue={audio_queue}")
    while not runScript.is_set():
        logger.debug("Audio player is running")
        try:
            pcm_data, samplerate, jsonFile = audio_queue.get(timeout=1)  # Get next audio data from the queue
            logger.debug(f"Got audio data from queue: {pcm_data}")
        except queue.Empty:
            continue # Continue to the next iteration of the loop, so it can check if the script should be running again.

        # Write to a WAV file in memory
        audio_file = io.BytesIO()
        write(audio_file, samplerate, pcm_data)
        audio_file.seek(0)  # reset file pointer to the beginning

        # Open the audio file
        wave_read = wave.open(audio_file, 'rb')

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Get the indices of your desired output devices
        speaker_output_index = get_device_index("Speakers (High Definition Audio")
        cable_output_index = get_device_index("CABLE Input (VB-Audio Virtual C")
        logger.debug(f"Speaker output index: {speaker_output_index}")
        logger.debug(f"Cable output index: {cable_output_index}")

        # Open a stream for the speakers
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
        
        logger.debug(f"Audio file details: {wave_read.getparams()}")
        logger.debug(f"Speaker stream details: {speaker_stream.get_output_latency()}")
        logger.debug(f"Cable stream details: {cable_stream.get_output_latency()}")

        # Play the stream
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
        speaker_stream.stop_stream()
        speaker_stream.close()
        cable_stream.stop_stream()
        cable_stream.close()

        # Terminate PyAudio
        p.terminate()

        logger.debug("Finished playing audio")

        # Simulate a mouse click to progress the message in FF14
        if jsonFile.get('Source') == 'AddonTalk':
            cooldownTime = 4  # Cooldown time in seconds
            logger.debug(f"Simulating mouse click with cooldown time {cooldownTime}")
            logger.debug(f"Mouse event occurred time check: {time.time() - mouse_event_occurred}")
            logger.debug(f"Keyboard event occurred time check: {time.time() - keyboard_event_occurred}")
            if time.time() - mouse_event_occurred > cooldownTime and time.time() - keyboard_event_occurred > cooldownTime:
                pyautogui.click(680, 1041)  # random point in main monitor between my 2 monitors, your mileage may vary

            # Reset the flags
            mouse_event_occurred = False
            keyboard_event_occurred = False

        # Indicate that the task is done
        audio_queue.task_done()