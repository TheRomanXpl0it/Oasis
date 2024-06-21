import requests
from pprint import pprint

TEAM_TOKEN = 'cccc'

flags = [

	# 'A' * 31 + '=',
	# 'B' * 31 + '=',
	# 'C' * 31 + '=',
	# 'D' * 31 + '=',
	# 'E' * 31 + '=',
	# 'E' * 31 + '=',
	# 'F' * 31 + '=',
	# 'G' * 31 + '=',
	# 'H' * 31 + '=',
	"PBDZT12PV0JIF3GHACXOTM7472GPOYN=",
]

IP = "10.10.0.1"
URL = f'http://{IP}:8080/flags'
FLAGIDS = f'http://{IP}:8081/flagIds'

headers = {
	'X-Team-Token': TEAM_TOKEN,
}

#r = requests.get(FLAGIDS + "?service=Polls&team=10.60.2.1", headers=headers)
r = requests.put(URL, headers=headers, json=flags)

print(r)
pprint(r.json())
