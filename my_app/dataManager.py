# TODO: create a modual for managing data. 99% of what you need is in main.py
# Function to set up JSON paths, this is so test.py can run while in another folder.
import os


def setup_json_paths():
    # Assuming that 'dataManager.py' is located in the 'my_app' directory
    # and the 'data' directory is at the root of your project
    main_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # Go up two levels
    paths = {
        'DICT_JSON_PATH': os.path.join(main_dir, 'data', 'dict.json'),
        'FEMALE_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'femaleVoices.json'),
        'FUNNY_NAMES_JSON_PATH': os.path.join(main_dir, 'data', 'funnyNames.json'),
        'IMPORTANT_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'importantVoices.json'),
        'MALE_VOICES_JSON_PATH': os.path.join(main_dir, 'data', 'maleVoices.json'),
        'SYMBOLS_AND_EMOTES_JSON_PATH': os.path.join(main_dir, 'data', 'symbolsAndEmotes.json'),
    }
    return paths

