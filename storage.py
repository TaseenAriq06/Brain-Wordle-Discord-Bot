import json
import os

STATS_FILE = 'stats.json' # name of the file to store user's data

def _load_data(): # check if the file already exists so it doesn't crash
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {} # if file is corrupted or empty return empty dictionary
    
def _save_data(data):
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f, indent = 4) # indent 4 makes it easier to read

def get_stats(user_id): # retrieves stats for a specific user
    data = _load_data()
        # JSON keys must be strings, Discord ID are integers, convert ID into a string
    user_id = str(user_id) 
        # .get() allows us to provide default values if user never played before
    return data.get(user_id, {"wins": 0, "losses": 0, "streak": 0, "max_streak": 0}) 

def update_stat(user_id, result):
    data = _load_data()             # load current data
    user_id = str(user_id)          

    if user_id not in data:         # initialize if user's stats don't exist yet
        data[user_id] = {"wins": 0, "losses": 0, "streak": 0, "max_streak": 0}

    if result == 'win':
        data[user_id]["wins"] += 1  # update user's win count by 1 if result equals the target word
        data[user_id]["streak"] += 1

        if data[user_id]["streak"] > data[user_id]["max_streak"]: # if streak becomes bigger than max streak, update max streak
            data[user_id]["max_streak"] = data[user_id]["streak"]
    elif result == 'loss':
        data[user_id]["losses"] += 1 # if user loses, update loss by 1 and reset current streak
        data[user_id]["streak"] = 0
    
    _save_data(data)                 # save the data back to the file
