import requests
import json
import pandas as pd
api_key = '1fd10942-b3bb-481e-807a-7bd09c4ed64a'


code_insee = {
 'paris':'75056',
 'nantes':'44109',
 'fromentine_la_barre-de-monts':'85012',
 'saint-gilles-croix-de-vie':'85222'
}

departure_name = 'paris'
departure = code_insee[departure_name]
arrival_name = 'fromentine_la_barre-de-monts'
arrival = code_insee[arrival_name]
aaaa_mm_dd = '20250909'
hhmmss = '070000'
logic = 'arrival' # (or departure) Here we want to align this with the earliest arrival time at Fromentine la Barre de Monts
min_options = 8
URL = f'https://api.sncf.com/v1/coverage/sncf/journeys?from=admin:fr:{departure}&to=admin:fr:{arrival}&datetime={aaaa_mm_dd}T{hhmmss}&datetime_represents={logic}&min_nb_journeys={min_options}'

HEADERS = {
 'Authorization' : api_key
}


r = requests.get(url=URL, headers=HEADERS)

data = r.json()

with open ('sncf_output.json', 'w') as j:
    json.dump(data, j, indent =4)


journeys = data.get("journeys", [])

# Extract only relevant fields for pd Dataframe
records = []
for j in journeys:
    records.append({
        "departure_time": j.get("departure_date_time"),
        "arrival_time": j.get("arrival_date_time"),
        "nb_transfers": j.get("nb_transfers")
    })

# Convert to DataFrame
df = pd.DataFrame(records)

# (Optional) Format datetime strings into pandas datetime objects
df["departure_time"] = pd.to_datetime(df["departure_time"], format="%Y%m%dT%H%M%S")
df["arrival_time"] = pd.to_datetime(df["arrival_time"], format="%Y%m%dT%H%M%S")
df["target_arrival_time"] = pd.to_datetime(f"{aaaa_mm_dd}T{hhmmss}", format="%Y%m%dT%H%M%S")
df["departure_name"] = departure_name
df["arrival_name"] = arrival_name
print(df)