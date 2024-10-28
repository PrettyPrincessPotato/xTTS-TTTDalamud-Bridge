import logging
import pygame
import threading
import my_app.queueManager as qM
import my_app.audioPlayer as aP

# Set up logging
logger = logging.getLogger(__name__)

# Define this function as the CLI thread.
def commands(runScript, procces_request_thread, main_thread, play_audio_thread):    
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
            qM.clear_queue(qM.request_queue)
            qM.clear_queue(qM.audio_queue)
            
            for thread in threading.enumerate():
                logger.debug(thread.name)
            logger.debug("Attempting to join procces_request_thread")
            procces_request_thread.join()
            logger.debug("Joined procces_request_thread")
            main_thread.join()
            aP.stop_pygame_mixer()  
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
            print("===== pause =====")
            print("Pauses audio playback.")
            print("===== play =====")
            print("Plays audio.")
            print("===== exit =====")
            print("exits the program.")

        elif command == "play":
            print("Playing...")
            pygame.mixer.music.unpause()
        
        elif command == "pause":
            print("Pausing...")
            pygame.mixer.music.pause()

        elif command == "skip":
            print("Skipping track...") # -- Initial testing, broken.
            aP.stop_pygame_mixer()
        
        elif command == "stop":
            print("Stopping...")
            qM.clear_queue()
            aP.stop_pygame_mixer()