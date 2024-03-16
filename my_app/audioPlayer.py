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
import os
import numpy as np
from scipy.io.wavfile import write
from pynput import mouse, keyboard
import pygame

# Set up logging
logger = logging.getLogger(__name__)

os.environ['SDL_AUDIODRIVER'] = 'directsound'  # 'directsound' or 'alsa' or 'pulse' depending on your system
import pygame.mixer

# Define the audio player function
def run_wav(audio_filepath):
    pygame.mixer.init(devicename = "CABLE Input (VB-Audio Virtual Cable)")
    pygame.mixer.music.load(audio_filepath)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    pygame.mixer.quit()

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
    while not runScript.is_set():
        try:
            audio_data, jsonFile = audio_queue.get(timeout=1)  # Get next audio data from the queue
            logger.debug(f"Got audio data from queue: {audio_data}")
        except queue.Empty:
            continue
        audio_file_dir = os.path.abspath("audio_files/audio_file.wav")

        # Write to a WAV file on disk
        with open(audio_file_dir, "wb") as f:
            f.write(audio_data)
        logger.debug("Audio data written to file")

        # Play the audio file
        # audio = AudioSegment.from_wav(audio_file_dir)
        # play(audio)
        logger.debug("Audio started playing")
        run_wav(audio_file_dir)
        logger.debug("Audio finished playing")
        
        # Simulate a mouse click to progress the message in FF14
        if jsonFile.get('Source') == 'AddonTalk':
            cooldownTime = 4  # Cooldown time in seconds
            logger.debug(f"Simulating mouse click with cooldown time {cooldownTime}")
            logger.debug(f"Mouse event occurred time check: {time.time() - mouse_event_occurred}")
            logger.debug(f"Keyboard event occurred time check: {time.time() - keyboard_event_occurred}")
            if time.time() - mouse_event_occurred > cooldownTime and time.time() - keyboard_event_occurred > cooldownTime:
                pyautogui.click(680, 1041)  # random point in main monitor between my 2 monitors, your mileage may vary
        # indicate that the task is done
        audio_queue.task_done()