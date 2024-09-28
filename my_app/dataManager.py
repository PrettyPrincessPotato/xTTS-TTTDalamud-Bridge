'''The following code defines a modular setup for managing different types of data in a unified manner. 
The purpose of this module is to provide an easy way to access and manage data across multiple scripts in an organized manner.
As of writing, the module is incomplete and is a work in progress, and it only really does one thing so far.
'''

# Function to set up JSON paths, this is so test.py can run while in another folder.
import json
import os
import logging
import random
import roman
import csv

# Set up logging
logger = logging.getLogger(__name__)

def get_csv():
    # Defines the path to the CSV file which is the TTS server URL
    # url should look something like https://ttsapi.ligma.com/tts_to_audio
    csv_file_path = './secretKeys/URL.csv'

    # Loads the private CSV so that the TTS server URL doesn't get leaked
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        # Since the CSV contains only one line with the URL, we can use next() to read it
        url = next(csv_reader)[0]  # This assumes the URL is in the first column
        return url


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

# Set up the JSON paths
json_paths = setup_json_paths()

# Use the paths from the dictionary
DICT_JSON_PATH = json_paths['DICT_JSON_PATH']
FEMALE_VOICES_JSON_PATH = json_paths['FEMALE_VOICES_JSON_PATH']
FUNNY_NAMES_JSON_PATH = json_paths['FUNNY_NAMES_JSON_PATH']
IMPORTANT_VOICES_JSON_PATH = json_paths['IMPORTANT_VOICES_JSON_PATH']
MALE_VOICES_JSON_PATH = json_paths['MALE_VOICES_JSON_PATH']
SYMBOLS_AND_EMOTES_JSON_PATH = json_paths['SYMBOLS_AND_EMOTES_JSON_PATH']

'''
    I'll be honest, I forget why the above code is here, but I'm sure there is a reason. I'm just going to leave it here.
    Probably fixing paths in case someone has a weird setup. Or perhaps makes it OS-independent. All I know is that it works.
'''

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