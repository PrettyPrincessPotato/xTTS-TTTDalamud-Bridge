############################################
# THIS SCRIPT MERGES JSON KEYS INTO DICTS  #
# CURRENT USE CASE:                        #
# CHANGE FUNNY NAMES TO USE MULTIPLE KEYS  #
############################################
import json
from collections import defaultdict

json_name = 'funnyNames.json'

# Create a defaultdict with an empty list as the default value
merged_dict = defaultdict(list)

# Open the JSON file and read it line by line
with open(json_name, 'r') as f:
    for line in f:
        # Remove whitespace from the beginning and end of the line
        line = line.strip()
        # If the line contains a key-value pair, add the value to the list of the corresponding key
        if ':' in line:
            key, value = line.split(':', 1)
            # Remove whitespace and quotes from the key and value
            key = key.strip().strip('"')
            value = value.strip().strip('",')
            merged_dict[key].append(value)

# Convert the defaultdict back to a regular dictionary
merged_dict = dict(merged_dict)

# Save the merged dictionary back to the JSON file
with open(json_name, 'w') as f:
    json.dump(merged_dict, f, indent=4)