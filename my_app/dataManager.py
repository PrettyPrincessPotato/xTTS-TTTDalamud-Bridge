'''The following code defines a modular setup for managing different types of data in a unified manner. 
The purpose of this module is to provide an easy way to access and manage data across multiple scripts in an organized manner.
As of writing, the module is incomplete and is a work in progress, and it only really does one thing so far.
'''

# TODO: create a modual for managing data. 99% of what you need is in main.py
# Function to set up JSON paths, this is so test.py can run while in another folder.
import os


def setup_json_paths():
    # Assuming that 'dataManager.py' is located in the 'my_app' directory
    # and the 'data' directory is at the root of your project
    main_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # Go up two levels
    paths = {
        # DICT_JSON is used to translate words to something the TTS can pronounce.
        'DICT_JSON_PATH': os.path.join(main_dir, 'data', 'dict.json'),
        # FEMALE_VOICES is a list of random female voices to be assigned to a user or npc.
        'FEMALE_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'femaleVoices.json'),
        # FUNNY_NAMES is similar to dict.json, but it's used to translate a word to a funny word. "Names" is a bit of a misnomer.
        'FUNNY_NAMES_JSON_PATH': os.path.join(main_dir, 'data', 'funnyNames.json'),
        # IMPORTANT_VOICES is a list of voices already saved and processed.
        'IMPORTANT_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'importantVoices.json'),
        # MALE_VOICES is a list of random male voices to be assigned to a user or npc.
        'MALE_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'maleVoices.json'),
        # SYMBOLS_AND_EMOTES is the same thing as dict, but called earlier in the process and translates specifically symbols and emotes.
        'SYMBOLS_AND_EMOTES_JSON_PATH': os.path.join(main_dir, 'data', 'symbolsAndEmotes.json'),
    }
    return paths

