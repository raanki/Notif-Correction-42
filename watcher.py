"""Watch for a 42 correction slot. Author: tmarx."""

if (__name__ != "__main__"):
    exit(1)
from sys import platform
if platform == 'win32':
    from win10toast import ToastNotifier
elif platform == 'darwin':
    import pync
elif platform == "linux":
    import notify2
import time
import requests
import datetime
import pickle

from dateutil import parser

# Time waited between every check, in seconds
WAIT_TIME = 15

def get_params():
    """Get the last params saved on the disk. Return None if no params saved."""
    try:
        with open("./params.pkl", "rb") as file:
            url, team_id, token, api = pickle.load(file)
            return (url, team_id, token, api)
    except:
        return (None, None, None, None)

def save_params(url, team_id, token, api):
    """Save params on the disk."""
    with open("./params.pkl", "wb+") as file:
        pickle.dump((url, team_id, token, api), file)

def notify(title, message):
    """Send a desktop notification."""
    if platform == 'darwin':
        pync.notify(message, title=title, contentImage="./logo.png", sound="default")
    elif platform == 'win32':
        toast = ToastNotifier()
        toast.show_toast(title, message, duration=0)
    elif platform == "linux":
        notify2.init("42 School Correction")
        n = notify2.Notification(title, message)
        n.show()

def get_slots():
    """Send a request to 42 intra."""
    today = datetime.date.today()
    start = today
    end = today + datetime.timedelta(days=days_to_watch)
    #print(f"Getting slots from {today} to {end}")
    request = requests.get(
        f"https://projects.intra.42.fr/projects/{project_url}/slots.json?team_id={team_id}&start={today}&end={end}",
        headers={
            "Host": "projects.intra.42.fr",
            "Cookie": f"_intra_42_session_production={token};"
        }
    )
    response = request.json()
    # print(response)
    if ("error" in response):
        print("Unable to connect, check the token!")
        exit(0)
    
    # Nouveau code pour traiter la réponse
    for slot in response:
        start_time = parser.parse(slot['start'])
        end_time = parser.parse(slot['end'])
        print(f"start: {start_time.hour}:{start_time.minute:02d}, end: {end_time.hour}:{end_time.minute:02d}")

    return response

# Do the callback if specified
def call_api(message):
    try:
        requests.get(api.format(message))
    except Exception as e:
        print(e)

# Check if we previously saved params
previous_url, previous_team_id, previous_token, previous_api = get_params()

url_placeholder = ""
team_id_placeholder = ""
token_placeholder = ""
api_placeholder = ""
if (not previous_url is None):
    url_placeholder = f" (default {previous_url})"
if (not previous_team_id is None):
    team_id_placeholder = f" (default {previous_team_id})"
if (not previous_token is None):
    token_placeholder = f" (default {previous_token})"
if (not previous_api is None):
    api_placeholder = f" (default {previous_api})"

# Get variables
print("Refer to ReadMe.md to help you find the following data.")

project_url = input(f"Project URL{url_placeholder}: ")
if (project_url == ""):
    project_url = previous_url

team_id = input(f"Team ID{team_id_placeholder}: ")
if (team_id == ""):
    team_id = previous_team_id

token = input(f"Session token{token_placeholder}: ")
if (token == ""):
    token = previous_token

api = input(f"API callback (optional){api_placeholder}: ")
if (api == ""):
    api = previous_api

try:
    days_to_watch = int(input("Number of days you want to watch (default 3): "))
except:
    days_to_watch = 3

save_params(project_url, team_id, token, api)

notify("Running", "You'll be notified when an open slot is found.")

notified_slot_times = set()

while True:
    print("\n\nChecking...")
    slots = get_slots()
    new_slots_found = False

    for slot in slots:
        start_time = parser.parse(slot['start'])
        end_time = parser.parse(slot['end'])
        slot_time_str = f"{start_time.hour}:{start_time.minute:02d} - {end_time.hour}:{end_time.minute:02d}"

        if slot_time_str not in notified_slot_times:
            new_slots_found = True
            notified_slot_times.add(slot_time_str)

            notify("Correction found!", f"New open slot found at: {slot_time_str}")
            if api:
                call_api("42: Correction Found")

    if not new_slots_found:
        print("No new slots found.")
    time.sleep(WAIT_TIME)
