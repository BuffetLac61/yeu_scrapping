import requests
import json
import pandas as pd
import sys
#api_key = '1fd10942-b3bb-481e-807a-7bd09c4ed64a'
if len(sys.argv) != 8:
    raise ValueError("You must provide exactly 5 arguments: api_key, departure_name(paris/nantes/fromentine_la_barre-de-monts) , arrival_name (idem...), date (aaaammdd), time (hhmmss), logic (departure/arrival), output json file (output.json)")

api_key = sys.argv[1]

code_insee = {
 'paris':'75056',
 'nantes':'44109',
 'fromentine_la_barre-de-monts':'85012',
 'saint-gilles-croix-de-vie':'85222'
}

departure_name = sys.argv[2]
departure = code_insee[departure_name]
arrival_name = sys.argv[3]
arrival = code_insee[arrival_name]
aaaammdd = sys.argv[4]
hhmmss = sys.argv[5]
logic = sys.argv[6] # (or departure) Arrival means we want to align this with the closest arrival time to the target time
output_file = sys.argv[7]

min_options = 8
URL = f'https://api.sncf.com/v1/coverage/sncf/journeys?from=admin:fr:{departure}&to=admin:fr:{arrival}&datetime={aaaammdd}T{hhmmss}&datetime_represents={logic}&min_nb_journeys={min_options}'

HEADERS = {
 'Authorization' : api_key
}


r = requests.get(url=URL, headers=HEADERS)

data = r.json()

with open ('sncf_outputraw.json', 'w') as j:
    json.dump(data, j, indent =4)


journeys = data.get("journeys", [])

# Extract only relevant fields for pd Dataframe
records = []
N = len(journeys)
for j in journeys:
    print(f"[-] Processing journey {len(records)+1} of {N}")
    places = []
    sections = j.get("sections")
    for section in sections:
        jplace = section.get("to", {}) # Sometimes "to" field is empty for a "waiting" section wich we can just ignore
        place = jplace.get("name")
        if place: #not doing anything if this is a waiting section with no "to" field
            places.append(place)
    
    records.append({
        "departure_time": j.get("departure_date_time"),
        "arrival_time": j.get("arrival_date_time"),
        "nb_transfers": j.get("nb_transfers"),
        "details": " -> ".join(places)
    })



# Convert to DataFrame
df = pd.DataFrame(records)

# Format datetime strings into pandas datetime objects
df["departure_time"] = pd.to_datetime(df["departure_time"], format="%Y%m%dT%H%M%S")
df["arrival_time"] = pd.to_datetime(df["arrival_time"], format="%Y%m%dT%H%M%S")
df["target_arrival_time"] = pd.to_datetime(f"{aaaammdd}T{hhmmss}", format="%Y%m%dT%H%M%S")
df["departure_name"] = departure_name
df["arrival_name"] = arrival_name

# REFormat them into string YYYY-MM-DD HH:MM:SS to stick to spider scrapy output items format
df["departure_time"] = df["departure_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
df["arrival_time"] = df["arrival_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
df["target_arrival_time"] = df["target_arrival_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")

json_str = df.to_json(orient="records", date_format="iso", indent=1)

# Write to a file
with open(output_file, "w", encoding="utf-8") as f: 
    f.write(json_str)

print("[+] JSON file saved as sncf_output.json")