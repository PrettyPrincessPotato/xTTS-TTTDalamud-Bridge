''' 
    TODO: create a module for the TTS to audio. 99% of what you need is in main.py
'''

# Import the required libraries
#import pyautogui # Disabled for now, as it is not working on Linux.
import time
import pydub
import queue
import logging
import os
# from pynput import mouse, keyboard
import pygame
import pygame.mixer

# Set up logging
logger = logging.getLogger(__name__)

os.environ['SDL_AUDIODRIVER'] = 'pulse'  # 'directsound' or 'alsa' or 'pulse' depending on your system

# Define the audio player function
def run_wav(audio_filepath):
    pygame.mixer.init(devicename = "game-sink")
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.load(audio_filepath)
    pygame.mixer.music.play()
    # sleep in case of lag and so music doesn't instantly end.
    time.sleep(0.3)
    while pygame.mixer.music.get_pos() > 0:
        pass
    pygame.mixer.quit()

# This will be set to True when the pause button is pressed.
pause_pressed = False

''' -- TEMPORARILY DISABLED, AS IT IS NOT WORKING ON LINUX -- 
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

def on_key_press(key):-- TEMPORARILY DISABLED, AS IT IS NOT WORKING ON LINUX --
    global keyboard_event_occurred
    keyboard_event_occurred = time.time()

# Start the mouse listener
listener = mouse.Listener(on_move=on_move, on_click=on_click)
listener.start()

# Start the keyboard listener
keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()
'''

############################################
# PLAY THE AUDIO AND SIMULATE MOUSE CLICK  #
############################################
def play_audio2(runScript, audio_queue):
    while not runScript.is_set():
        try:
            audio_data, jsonFile = audio_queue.get(timeout=1)  # Get next audio data from the queue
            logger.debug(f"Got audio data from queue: {audio_data}")
        except queue.Empty:
            continue
        audio_file_dir = os.path.abspath("xTTS-TTTDalamud-Bridge/audio_files/audio_file.wav")

        # Write to a WAV file on disk
        with open(audio_file_dir, "wb") as f:
            f.write(audio_data)
        logger.debug("Audio data written to file")

        # wav file needs to be transformed into a mp3 first for pydub to support pausing. .ogg also works, I have no reason behind mp3.
        wav_to_mp3(runScript, audio_file_dir)

        # set new audio file as the mp3 we just made
        audio_file_dir = os.path.abspath("xTTS-TTTDalamud-Bridge/audio_files/audio_file.mp3")

        # Play the audio file
        logger.debug("Audio started playing")
        run_wav(audio_file_dir)
        logger.debug("Audio finished playing")
        
        # indicate that the task is done
        audio_queue.task_done()

# Depreciated soon, will be replaced with play_audio2()
def play_audio(runScript, audio_queue):
    global mouse_event_occurred, keyboard_event_occurred
    while not runScript.is_set():
        try:
            audio_data, jsonFile = audio_queue.get(timeout=1)  # Get next audio data from the queue
            logger.debug(f"Got audio data from queue: {audio_data}")
        except queue.Empty:
            continue
        audio_file_dir = os.path.abspath("xTTS-TTTDalamud-Bridge/audio_files/audio_file.wav")

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
            ''' -- TEMPORARILY DISABLED, AS IT IS NOT WORKING ON LINUX --
            logger.debug(f"Mouse event occurred time check: {time.time() - mouse_event_occurred}")
            logger.debug(f"Keyboard event occurred time check: {time.time() - keyboard_event_occurred}")
             if time.time() - mouse_event_occurred > cooldownTime and time.time() - keyboard_event_occurred > cooldownTime: 
                pyautogui.click(680, 1041)  # random point in main monitor between my 2 monitors, your mileage may vary
                '''
        # indicate that the task is done
        audio_queue.task_done()

# This function changes wav files to mp3 files
def wav_to_mp3(runScript, wavFile):
    pydub.AudioSegment.from_wav(wavFile).export(wavFile[:-4] + ".mp3", format="mp3")