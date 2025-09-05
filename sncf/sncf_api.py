import requests
import json
api_key = '1fd10942-b3bb-481e-807a-7bd09c4ed64a'



code_insee = {
 'paris':'75056',
 'nantes':'44109',
 'fromentine_la_barre-de-monts':'85012',
 'saint-gilles-croix-de-vie':'85222'
}

departure = code_insee['nantes']
arrival = code_insee['fromentine_la_barre-de-monts']
aaaa_mm_dd = '20250907'
hhmmss = '070000'
logic = 'arrival' # (or departure) Here we want to align this with the earliest arrival time at Fromentine la Barre de Monts
min_options = 1
URL = f'https://api.sncf.com/v1/coverage/sncf/journeys?from=admin:fr:{departure}&to=admin:fr:{arrival}&datetime={aaaa_mm_dd}T{hhmmss}&datetime_represents={logic}&min_nb_journeys={min_options}'

HEADERS = {
 'Authorization' : api_key
}


r = requests.get(url=URL, headers=HEADERS)

data = r.json()

with open ('output.json', 'w') as j:
    json.dump(data, j, indent =4)

print(r)
print(data)