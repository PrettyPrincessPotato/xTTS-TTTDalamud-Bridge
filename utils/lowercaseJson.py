import json

jsonName = 'funnyNames.json'

# Load the data from the JSON file
with open(jsonName, 'r') as f:
    data = json.load(f)

# Create a new dictionary with all lowercase keys
lowercase_data = {key.lower(): value for key, value in data.items()}

# Write the new dictionary back to the JSON file
with open(jsonName, 'w') as f:
    json.dump(lowercase_data, f, indent=4)