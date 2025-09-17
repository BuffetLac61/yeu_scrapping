# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
import pandas as pd
from datetime import datetime, timedelta

# Robust month map (with or without accents exception handled)
MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
    "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
}

class YeuPipeline:

    def _parse_text_date(self, raw_date: str, fallback_year: int):
        # par exemlpe : "Lundi 01 Septembre"
        m = re.search(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)", (raw_date or ""))
        if not m:
            print(f"[!] Couldn't parse text date from: {raw_date!r}")
            return None
        day = int(m.group(1))
        month_name = m.group(2).lower()
        month = MONTHS.get(month_name)
        if not month:
            print(f"[!] Unknown month name: {month_name!r}")
            return None
        return datetime(fallback_year, month, day)
    

    def process_item(self, item, spider):

        """
        Each scrapped items from yc_boat spiderlooks like this :
        {
          "title_debug": ["Réservez votre passage"],
          "date": ["Lundi 01 Septembre"],
          "horaire_link": ["/ws?func=set_args&voyage=2VERS1&date[]=20250901.630"],
          "arrival": ["Arrivée à Yeu vers 07:00"]
        }
        We are going to extract starting location , arrival loation and departure datetime from "horaire_link" field.
        We are going to extract arrival time from 'arrival' field
        We are going to auto check our regex using the date field (double check basically...)
        """
        print("\n[-] Analysing date : " + item['date'][0])
        raw_date = (item.get("date") or [""])[0]
        raw_link = (item.get("horaire_link") or [""])[0]
        raw_arrival = (item.get("arrival") or [""])[0]

        # Parse YYYYMMDD.HHMM (HHMM can be 3 or 4 digits; last two are minutes)
        m = re.search(r"date\[\]=(?P<date>\d{8})\.(?P<hhmm>\d{1,4})", raw_link)
        if not m:
            print(f"[!] horaire_link field does not match expected pattern: {raw_link!r}")
            return {"departure_time": None, "arrival_time": None, "nb_transfers": 0}

        date_str = m.group("date")  # "20250901"
        hhmm = m.group("hhmm")      # "630" -> 06:30, "1630" -> 16:30, etc.

        year = int(date_str[:4])
        month_link = int(date_str[4:6])
        day_link = int(date_str[6:8])

        minutes = int(hhmm[-2:])
        hours = int(hhmm[:-2] or "0")
        if hours > 23 or minutes > 59:
            print(f"[!] Invalid hhmm '{hhmm}' in link {raw_link!r}")

        departure_time = datetime(year, month_link, day_link, hours, minutes)

        # Double-check text date vs link date
        text_date_dt = self._parse_text_date(raw_date, fallback_year=year)
        if text_date_dt:
            if (text_date_dt.year, text_date_dt.month, text_date_dt.day) != (year, month_link, day_link):
                print(
                    f"[!] Date mismatch - "
                    f"link={year:04d}-{month_link:02d}-{day_link:02d} "
                    f"vs text={text_date_dt:%Y-%m-%d} "
                    f"(raw_date={raw_date!r}, link={raw_link!r})"
                )
        else:
            print(f"[!] Skipping text-date check (couldn't parse) for raw_date={raw_date!r}")

        # Arrival time (same day by default; roll over if needed)
        m2 = re.search(r"(\d{1,2}):(\d{2})", raw_arrival or "")
        if m2:
            ah, am = int(m2.group(1)), int(m2.group(2))
            arrival_time = departure_time.replace(hour=ah, minute=am)
            if arrival_time < departure_time:
                arrival_time += timedelta(days=1)  # handle over-midnight edge case
        else:
            print(f"[!] Couldn't parse arrival time from: {raw_arrival!r}")
            arrival_time = None

        item["departure_time"] = pd.to_datetime(departure_time).strftime("%Y-%m-%dT%H:%M:%S") if departure_time else None
        item["arrival_time"] = pd.to_datetime(arrival_time).strftime("%Y-%m-%dT%H:%M:%S") if arrival_time else None
        item["nb_transfers"] = 0

                # New part: extract voyage direction from horaire_link
        voyage_match = re.search(r"voyage=(\dVERS\d)", raw_link)
        if voyage_match:
            voyage = voyage_match.group(1)
            if voyage == "1VERS2":
                item["departure_name"] = "yeu"
                item["arrival_name"] = "fromentine_la_barre-de-monts"
                item["details"] = "yeu -> fromentine_la_barre-de-monts"
            elif voyage == "2VERS1":
                item["departure_name"] = "fromentine_la_barre-de-monts"
                item["arrival_name"] = "yeu"
                item["details"] = "fromentine_la_barre-de-monts -> yeu"
            else:
                item["departure_name"] = None
                item["arrival_name"] = None
        else:
            print(f"[!] Couldn't parse voyage from horaire_link: {raw_link!r}")
            item["departure_name"] = None
            item["arrival_name"] = None

        # Same schema as the SNCF dataframe
        return item