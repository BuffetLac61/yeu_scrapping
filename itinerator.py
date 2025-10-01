import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

def run_sncf_api(
    sncf_token: str, dep: str, arr: str,
    target_dt: datetime, logic: str,
    output_file: str
) -> List[Dict[str, Any]]:
    """Call from sncf dir , sncf_api.py with an output file and return a list composed of the parsed JSON results OR an empty list if an error occured or if no voyage suitable is found."""
    cmd = [
        "python", "sncf_api.py",
        sncf_token, dep, arr,
        target_dt.strftime("%Y%m%d"), target_dt.strftime("%H%M%S"),
        logic, output_file
    ]
    print(f"[-] Running SNCF API command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd="sncf", capture_output=True, text=True)

    if res.returncode == 5:
        print(f"[!] No suitable voyage found")
        return []
    
    if res.returncode != 0:
        print(f"[!] SNCF API error: {res.stderr}")
        return []

    try:
        with open(f"./sncf/{output_file}","r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Failed to load {output_file}: {e}")
        return []

def run_boat_spider(date_str: str) -> List[Dict[str, Any]]:
    """
    Call the yc_boat spider from the scrapy folder "yeu" for a given date and return a list of dictionaries containing the parsed JSON results, 
    or an empty list if no suitable passage is found.
    """

    cmd = [
        "scrapy", "crawl", "yc_boat",
        "-a", f"date={date_str}",
        "-O", "boats.json"
    ]

    print(f"[-] Fetching : {' '.join(cmd)}")
    print(f"[-] Running boat spider command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd="yeu", capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Boat spider error: {res.stderr}")
        return []

    try:
        with open("./yeu/boats.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Failed to load boats.json: {e}")
        return []

def parse_iso(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")



def choose_best_connection(
    options: List[Dict[str, Any]], 
    target: datetime, 
    mode: str
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """
    Pick the option whose departure/arrival is closest to the target.
    mode="arrival" -> arrival closest to target and not after.
    mode="departure" -> departure closest to target and not before.
    Returns (index, option) or None if no option is found.
    """
    if not options:
        return None

    if mode == "arrival":
        valid = [(i, o) for i, o in enumerate(options) if parse_iso(o["arrival_time"]) <= target]
        if not valid:
            return None
        return min(valid, key=lambda x: parse_iso(x[1]["arrival_time"]) - target)
    else:
        valid = [(i, o) for i, o in enumerate(options) if parse_iso(o["departure_time"]) >= target]
        if not valid:
            return None
        return min(valid, key=lambda x: parse_iso(x[1]["departure_time"]) - target)



def plan_voyage_outbound(sncf_token: str, user_start: datetime, boats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []

    # -------- OUTBOUND --------
    # Boat closest to user_start + 3h (we assume we can't find any connexion options better than a 3H from Paris to fromentine so no need to try and loop over earlier boat options)
    target_boat_time = user_start + timedelta(hours=3)
    outbound_boats = [b for b in boats if b["departure_name"] == "fromentine_la_barre-de-monts"]
    outbound_boats = [b for b in outbound_boats if parse_iso(b["departure_time"]) >= target_boat_time] # We prefiltred boats to only outbounds one with departure time at user_start + 3h or later (useless to try earlier, no combination of train and ar will be found)
    if not outbound_boats:
        print("[!] No outbound boats found.") # We can't go to Yeu this month
        return []
    outbound_boats = sorted(outbound_boats, key=lambda b: abs(parse_iso(b["departure_time"]) - target_boat_time)) # We order Boats by departure time closest to target time and we will try each one in order until we find a suitable car + train combination to go with it
    
    i = 0
    chosen_car = None
    chosen_train = None
    while chosen_train is None:
        chosen_boat = outbound_boats[i]
        print(f"[+] Boat option found departs at {chosen_boat['departure_time']} (target was {target_boat_time}), trying to align a car")
        # Car Nantes -> Fromentine. Car arrival (arrival logic for SNCF API) aligned with boat departure time
        boat_dt = parse_iso(chosen_boat["departure_time"])
        car_options = run_sncf_api(sncf_token, "nantes", "fromentine_la_barre-de-monts", boat_dt, "arrival", "car_outbound.json")
        car_options = [c for c in car_options if parse_iso(c["arrival_time"]) <= boat_dt - timedelta(minutes=5)] # We need to arrive at least 5min before the boat departure
        chosen_idx_car = choose_best_connection(car_options, boat_dt, mode="arrival") # index and option found or None if no car found
        
        while chosen_train is None and len(car_options) > 0: # We will try each car option until we find a suitable train or we run out of car options
            if chosen_idx_car is None: # If no car is found we directly try the next boat option
                print("[!] No suitable car found for this boat option, trying next boat option")
                break
            else : 
                idx_car, chosen_car = chosen_idx_car
                print(f"[+] Car option found departs at {chosen_car['departure_time']}, trying to align a train")
                # Train Paris -> Nantes aligned with car departure
                car_dt = parse_iso(chosen_car["departure_time"])
                train_options = run_sncf_api(sncf_token, "paris", "nantes", car_dt, "arrival", "train_outbound.json")
                train_options = [t for t in train_options if parse_iso(t["arrival_time"]) <= car_dt - timedelta(minutes=5)] # We need to arrive at least 5min before the car departure
                train_options = [t for t in train_options if parse_iso(t["departure_time"]) >= user_start] # We need to depart after user_start (when the user can be at earliest at Paris Montparnasse)
                chosen_idx_train = choose_best_connection(train_options, car_dt, mode="arrival")
                if chosen_idx_train:
                    idx_train, chosen_train = chosen_idx_train
                    print(f"✅ Train option found departs at {chosen_train['departure_time']}, voyage plan complete!")
                    # We found a complete plan
                    results.append(chosen_boat)
                    results.append(chosen_car)
                    results.append(chosen_train)
                elif chosen_idx_train is None:
                    car_options.pop(idx_car) # We remove this car option and try again without this last non viable option
                    chosen_idx_car = choose_best_connection(car_options, boat_dt, mode="arrival") # We do the same loop with the next best car option (if no options is found in car_otptions, chosen_idx_car will be None and the loop will try the next boat due to the break condition) (if car_options is empty chosen_idx_car will be None and the loop will try the next boat option as len(car_otpiions will be 0)
        
        i += 1 # We will try the next boat option
        print(f"[!] No suitable car + train found for this boat, trying next boat option")

    return results


def plan_voyage_return(sncf_token: str, user_end: datetime, boats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    # -------- Return --------
    # Boat closest to user_end - 3h (we assume we can't find any connexion options better than a 3H from fromentine to Paris so no need to try and loop over later boat options)
    target_boat_time = user_end - timedelta(hours=3)
    return_boats = [b for b in boats if b["departure_name"] != "fromentine_la_barre-de-monts"]
    return_boats = [b for b in return_boats if parse_iso(b["arrival_time"]) <= target_boat_time] # We prefiltred boats to only outbounds one with arrival time at user_start - 3h or before (useless to try earlier, no combination of train and car will be found)
    if not return_boats:
        print("[!] No outbound boats found.") # We can't go to Yeu this month
        return []
    return_boats = sorted(return_boats, key=lambda b: abs(parse_iso(b["arrival_time"]) - target_boat_time)) # We order Boats by arrival time closest to target time and we will try each one in order until we find a suitable car + train combination to go with it
    
    i = 0
    chosen_car = None
    chosen_train = None
    while chosen_train is None:
        chosen_boat = return_boats[i]
        print(f"[+] Boat option found arrival at {chosen_boat['arrival_time']} (target was {target_boat_time}), trying to align a car")
        # Car Nantes -> Fromentine. Car arrival (arrival logic for SNCF API) aligned with boat departure time
        boat_dt = parse_iso(chosen_boat["arrival_time"])
        car_options = run_sncf_api(sncf_token, "fromentine_la_barre-de-monts", "nantes", boat_dt, "departure", "car_return.json")
        car_options = [c for c in car_options if parse_iso(c["departure_time"]) >= boat_dt + timedelta(minutes=5)] # We need to depart at least 5min after the boat arrival
        chosen_idx_car = choose_best_connection(car_options, boat_dt, mode="departure") # index and option found or None if no car found
        
        while chosen_train is None and len(car_options) > 0: # We will try each car option until we find a suitable train or we run out of car options
            if chosen_idx_car is None: # If no car is found we directly try the next boat option
                print("[!] No suitable car found for this boat option, trying next boat option")
                break
            else : 
                idx_car, chosen_car = chosen_idx_car
                print(f"[+] Car option found departs at {chosen_car['departure_time']}, trying to align a train")
                # Train Nantes -> Paris aligned with car arrival
                car_dt = parse_iso(chosen_car["arrival_time"])
                train_options = run_sncf_api(sncf_token, "nantes", "paris", car_dt, "departure", "train_return.json")
                train_options = [t for t in train_options if parse_iso(t["arrival_time"]) >= car_dt + timedelta(minutes=5)] # We need to depart at least 5min after the car arrival
                train_options = [t for t in train_options if parse_iso(t["departure_time"]) <= user_end] # We need to arrive before user_end (when the user can be at latest at Paris Montparnasse)
                chosen_idx_train = choose_best_connection(train_options, car_dt, mode="departure")
                if chosen_idx_train:
                    idx_train, chosen_train = chosen_idx_train
                    print(f"✅ Train option found arrives at {chosen_train['arrival_time']}, return voyage plan complete!")
                    # We found a complete plan
                    results.append(chosen_boat)
                    results.append(chosen_car)
                    results.append(chosen_train)
                elif chosen_idx_train is None:
                    car_options.pop(idx_car) # We remove this car option and try again without this last non viable option
                    chosen_idx_car = choose_best_connection(car_options, boat_dt, mode="departure") # We do the same loop with the next best car option (if no options is found in car_otptions, chosen_idx_car will be None and the loop will try the next boat due to the break condition) (if car_options is empty chosen_idx_car will be None and the loop will try the next boat option as len(car_otpiions will be 0)
        
        i += 1 # We will try the next boat option
        print(f"[!] No suitable car + train found for this boat, trying next boat option")

    return results


if __name__ == "__main__":
    # Example usage
    sncf_token = "1fd10942-b3bb-481e-807a-7bd09c4ed64a"

    # User inputs
    user_start = datetime(2025, 10, 10, 19, 0, 0)  # Available at Paris Montparnasse
    user_end = datetime(2025, 10, 15, 8, 30, 0)   # Must be back at Paris Montparnasse

    run_boat_spider(user_start.strftime("%d/%m/%Y"))

    # Load boats.json
    with open("./yeu/boats.json", "r", encoding="utf-8") as f:
        boats = json.load(f)

    final_plan_outbound = plan_voyage_outbound(sncf_token, user_start, boats)
    final_plan_return = plan_voyage_return(sncf_token, user_end, boats)

    # Save summary
    with open("final_voyage_plan_outbound.json", "w", encoding="utf-8") as f:
        json.dump(final_plan_outbound, f, ensure_ascii=False, indent=2)

        # Save summary
    with open("final_voyage_plan_return.json", "w", encoding="utf-8") as f:
        json.dump(final_plan_return, f, ensure_ascii=False, indent=2)

    print("✅ Voyage plan saved to final_voyage_plan.json")
