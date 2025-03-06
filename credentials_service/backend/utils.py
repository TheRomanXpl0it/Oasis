import json
import os
from fasteners import InterProcessLock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = os.getenv('DEBUG', "0").strip() == "1"

TEAMS_DATA_FILE = os.path.join(BASE_DIR, 'oasis-setup-config.json' if not DEBUG else '../../oasis-setup-config.json')

config_file_lock = InterProcessLock(os.path.join(BASE_DIR, "teams_data.json.lock"))

def load_teams_data():
    with open(TEAMS_DATA_FILE, 'r') as f:
        return json.load(f)
    
def save_teams_data(data):
    with open(TEAMS_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def prepare_json_file(regenerate=False):
    with config_file_lock:
        data = load_teams_data()
        if not data.get('pin_data_added'):
            data['pin_data_added'] = True
        else:
            if not regenerate:
                return
        total_profiles = data['wireguard_profiles']
        created_pins = set()
        for i, team in enumerate(data['teams']):
            if team['nop']:
                continue
            data['teams'][i]['pins'] = []
            for j in range(total_profiles):
                pin = None
                while pin is None or pin in created_pins:
                    pin = int.from_bytes(os.urandom(6), 'big') % (10 ** 6)
                pin = str(pin).rjust(6, '0')
                created_pins.add(pin)
                data['teams'][i]['pins'].append({
                    'pin': pin,
                    'profile': j+1, 
                })
        save_teams_data(data)
        
def wireguard_path(team_id, profile_id):
    if DEBUG:
        return os.path.join(BASE_DIR, f'../../wireguard/conf{team_id}/peer{profile_id}/peer{profile_id}.conf')
    else:
        return os.path.join(BASE_DIR, f'wireguard/conf{team_id}/peer{profile_id}/peer{profile_id}.conf')