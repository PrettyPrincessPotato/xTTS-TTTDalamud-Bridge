import queue
import re
import io
import logging
import json
import random
import requests
import soundfile as sf
import my_app.dataManager as dM
import my_app.queueManager as qM
from requests import Request
from inflect import engine
from requests import Session

# Create an inflect engine, which is used to pluralize words.
inflect_engine = engine()

# Set up logging
logger = logging.getLogger(__name__)

# Stores the session as a variable so credentials are not needed to be entered every time.
s = Session()

url = dM.get_csv()

############################################
# PROCESS THE REQUESTS AND SEND TO SERVER  #
############################################
def process_request(runScript, request_queue):
    while not runScript.is_set():            
        try:
            # Get the next request from the request_queue
            jsonFile = request_queue.get(timeout=1) # Get the next request from the queue, but timeout after 1 second
            logger.debug("DEBUG: Got item from queue")
            logger.debug("DEBUG: jsonFile: ", jsonFile)
        except queue.Empty:  # If the queue is empty
            continue  # Continue to the next iteration of the loop, so it can check if the script should be running again.

        # Get the voice of the speaker.
        logger.debug("DEBUG: Getting voice")
        voice = dM.get_voice(jsonFile["Speaker"], jsonFile["Voice"].get("Name"), jsonFile.get("Source"))
        logger.debug("DEBUG: Got voice: ", voice)

        # Get the payload from the request
        payload = jsonFile["Payload"]
        logger.debug("DEBUG: Payload assigned from jsonFile. Payload:")
        logger.debug(payload)
        
        # replace symbols and emotes
        payload = dM.replace_symbols_and_emoticons(payload)
        logger.debug("DEBUG: Replaced symbols and emoticons to be phonetic. Payload: ")
        logger.debug(payload)

        # Split the payload into words and punctuation
        words_and_punctuation = re.findall(r"[\w'-]+|[.,!?;:-]", payload)
        logger.debug("DEBUG: Split payload into words and punctuation: ")
        logger.debug(words_and_punctuation)

        # Replace roman numerals to arabic
        words_and_punctuation = dM.convert_roman_numerals_to_arabic(words_and_punctuation)
        logger.debug("DEBUG: Converted Roman numerals to Arabic numerals. words_and_punctuation:")
        logger.debug(words_and_punctuation)

        # Create a list to store the corrected words and punctuation
        corrected_words_and_punctuation = []
        logger.debug("DEBUG: Created list to store corrected words and punctuation")
        logger.debug(corrected_words_and_punctuation)

        # Load the pronunciation dictionary
        with open(dM.DICT_JSON_PATH, 'r') as f:
            pronunciation_dict = json.load(f)
            logger.debug("DEBUG: Loaded pronunciation dictionary")
            logger.debug(pronunciation_dict)
                
        # Load the funny names dictionary
        with open(dM.FUNNY_NAMES_JSON_PATH, 'r') as f:
            funny_names_dict = json.load(f)
            logger.debug("DEBUG: Loaded funny names dictionary")
            logger.debug(funny_names_dict)

        # Iterate through the words and punctuation
        for word_or_punctuation in words_and_punctuation:
            logger.debug("DEBUG: Word being checked: ")
            logger.debug(word_or_punctuation)
            corrected = False  # Flag to check if the word has been corrected
            # If the word is in the funny names dictionary, occasionally replace it
            logger.debug("DEBUG: Corrected? - Before random chance for funny_names_dict:")
            logger.debug(corrected)
            if word_or_punctuation.lower() in funny_names_dict and random.random() < 0.01:  # 1% chance
                logger.debug("DEBUG: Congrats! You got the 1 percent chance for funny_names_dict!")
                logger.debug("DEBUG: Any more debugging is irrelivant for now, as the word being replaced is so hilariously different you would know if it worked.")
                logger.debug("DEBUG: this is an issue for later tater.")
                # Randomly select a replacement from the list
                corrected_word_or_punctuation = random.choice(funny_names_dict[word_or_punctuation.lower()])
                corrected = True  # Update the flag
            elif word_or_punctuation.lower().endswith('s') and word_or_punctuation.lower()[:-1] in funny_names_dict and random.random() < 0.01:  # 1% chance:
                logger.debug("DEBUG: Congrats! You got the 1 percent chance for funny_names_dict! (plural)")
                logger.debug("DEBUG: Any more debugging is irrelivant for now, as the word being replaced is so hilariously different you would know if it worked.")
                logger.debug("DEBUG: this is an issue for later tater.")
                # Randomly select a replacement from the list and pluralize it
                corrected_word_or_punctuation = inflect_engine.plural(random.choice(funny_names_dict[word_or_punctuation.lower()[:-1]]))
                corrected = True  # Update the flag

            if not corrected and word_or_punctuation.lower() in pronunciation_dict:
                corrected_word_or_punctuation = pronunciation_dict[word_or_punctuation.lower()]
                corrected = True  # Update the flag
            # Otherwise, keep the word or punctuation as it is
            if not corrected:
                corrected_word_or_punctuation = word_or_punctuation
            # Add the corrected word or punctuation to the list
            corrected_words_and_punctuation.append(corrected_word_or_punctuation)
        # Join the corrected words and punctuation back together
        corrected_payload = " ".join(corrected_words_and_punctuation)
        # Remove spaces before punctuation
        corrected_payload = corrected_payload.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?").replace(" ;", ";").replace(" :", ":").replace(" -", "-")  
        logger.debug("DEBUG: Corrected payload: ")
        logger.debug(corrected_payload)

        # Defines data, the json input required to get audio back
        logger.debug("DEBUG: Creating data dict")
        data_dict = {"text": corrected_payload, "speaker_wav": voice, "language": "en"}
        logger.debug("DEBUG: data_dict input: ", data_dict)
        data = json.dumps(data_dict)

        # defines req, a POST request using URL and Data to send that information.
        logger.debug("DEBUG: Creating request")
        req = Request('POST', url, data=data)
        # defines prepped, which requires the request to be prepared for some weird fuckin reason
        prepped = req.prepare()

        # defines resp, which is when we send the prepped request with Session()
        max_retries = 1
        for i in range(max_retries):
            try:
                resp = s.send(prepped)
                if resp.status_code != 200:  # Check if the status code is not 200
                    logger.error(f"Error: Received status code {resp.status_code} from TTS server. Response content:")
                    logger.error(resp.content.decode())  # Print the response content
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
            logger.error("Error: Unable to read response from TTS server as an audio file.")
            continue  # Skip the rest of this iteration and go back to the start of the loop

        qM.audio_queue.put((audio_data, jsonFile))  # Put the audio data in the audio queue, this should be a .wav file.