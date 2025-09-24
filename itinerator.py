import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def run_sncf_api(
    sncf_token: str, dep: str, arr: str,
    target_dt: datetime, logic: str,
    output_file: str
) -> List[Dict[str, Any]]:
    """Call from sncf dir , sncf_api.py with an output file and return parsed JSON results."""
    cmd = [
        "python", "sncf_api.py",
        sncf_token, dep, arr,
        target_dt.strftime("%Y%m%d"), target_dt.strftime("%H%M%S"),
        logic, output_file
    ]
    print(f"[-] Running SNCF API command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd="sncf", capture_output=True, text=True)
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
    """Call the yc_boat spider from the scrapy folder "yeu" for a given date and return parsed JSON results."""

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


def choose_best_connection(options: List[Dict[str, Any]], target: datetime, mode: str) -> Optional[Dict[str, Any]]:
    """
    Pick the option whose departure/arrival is closest to the target.
    mode="arrival" means arrival the closest to target and not after, 
    mode="departure" means departure the closest to the target but not before.
    """
    if not options:
        return None

    if mode == "arrival":
        # In "arrival" mode we are trying to find an arrival time the closest to the target (being the departure of the next transport
        options = [o for o in options if parse_iso(o["arrival_time"]) <= target] # We can't have an arrival of the previous transport after the target being the departure of the next transport
        return min(options, key=lambda x: parse_iso(x["arrival_time"]) - target)
    else:
        options = [o for o in options if parse_iso(o["departure_time"]) >= target] 
        return min(options, key=lambda x: parse_iso(x["departure_time"]) - target)  


def plan_voyage(sncf_token: str, user_start: datetime, user_end: datetime, boats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []

    # -------- OUTBOUND --------
    # Boat closest to user_start + 3h (we assume we can't find any connexion options better than a 3H from Paris to fromentine so no need to try and loop over earlier boat options)
    target_boat_time = user_start + timedelta(hours=3)
    outbound_boats = [b for b in boats if b["departure_name"] == "fromentine_la_barre-de-monts"]
    outbound_boats = [b for b in outbound_boats if parse_iso(b["departure_time"]) >= target_boat_time] # We prefiltred boats to only outbounds one and after user_start + 3h
    if not outbound_boats:
        print("[!] No outbound boats found.")
        return []

    chosen_boat = min(outbound_boats, key=lambda b: parse_iso(b["departure_time"]) - target_boat_time) 
    print(f"[+] Boat option found departs at {chosen_boat['departure_time']} (target was {target_boat_time}), trying to align a car")
    results.append(chosen_boat)

    # Car Nantes -> Fromentine. Car arrival (arrival logic for SNCF API) aligned with boat departure time
    boat_dt = parse_iso(chosen_boat["departure_time"])
    car_options = run_sncf_api(sncf_token, "nantes", "fromentine_la_barre-de-monts", boat_dt, "arrival", "car_outbound.json")
    chosen_car = choose_best_connection(car_options, boat_dt, mode="arrival")
    if chosen_car:
        results.append(chosen_car)

        # Train Paris -> Nantes aligned with car departure
        car_dt = parse_iso(chosen_car["departure_time"])
        train_options = run_sncf_api(sncf_token, "paris", "nantes", car_dt, "arrival", "train_outbound.json")
        chosen_train = choose_best_connection(train_options, car_dt, mode="arrival")
        if chosen_train:
            results.append(chosen_train)

    # -------- RETURN --------
    # Boat closest to user_end - 3h
    target_return_time = user_end - timedelta(hours=3)
    return_boats = [b for b in boats if b["arrival_name"] == "fromentine_la_barre-de-monts"]
    return_boats = [b for b in return_boats if parse_iso(b["arrival_time"]) <= target_return_time]
    if not return_boats:
        print("[!] No return boats found.")
        return results

    chosen_return_boat = min(return_boats, key=lambda b: abs(parse_iso(b["arrival_time"]) - target_return_time))
    results.append(chosen_return_boat)

    # Car Fromentine -> Nantes aligned with boat departure
    boat_arrival_dt = parse_iso(chosen_return_boat["arrival_time"])
    car_back_options = run_sncf_api(sncf_token, "fromentine_la_barre-de-monts", "nantes", boat_arrival_dt, "departure", "car_return.json")
    chosen_car_back = choose_best_connection(car_back_options, boat_arrival_dt, mode="departure")
    if chosen_car_back:
        results.append(chosen_car_back)

        # Train Nantes -> Paris aligned with car arrival
        car_back_arrival_dt = parse_iso(chosen_car_back["arrival_time"])
        train_back_options = run_sncf_api(sncf_token, "nantes", "paris", car_back_arrival_dt, "departure", "train_return.json")
        chosen_train_back = choose_best_connection(train_back_options, car_back_arrival_dt, mode="departure")
        if chosen_train_back:
            results.append(chosen_train_back)

    return results


if __name__ == "__main__":
    # Example usage
    sncf_token = "1fd10942-b3bb-481e-807a-7bd09c4ed64a"

    # User inputs
    user_start = datetime(2025, 9, 26, 19, 0, 0)  # Available at Paris Montparnasse
    user_end = datetime(2025, 9, 29, 8, 30, 0)   # Must be back at Paris Montparnasse

    run_boat_spider(user_start.strftime("%d/%m/%Y"))

    # Load boats.json
    with open("./yeu/boats.json", "r", encoding="utf-8") as f:
        boats = json.load(f)

    final_plan = plan_voyage(sncf_token, user_start, user_end, boats)

    # Save summary
    with open("final_voyage_plan.json", "w", encoding="utf-8") as f:
        json.dump(final_plan, f, ensure_ascii=False, indent=2)

    print("✅ Voyage plan saved to final_voyage_plan.json")
