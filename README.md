# 🚤 Paris → Île d’Yeu Trip Planner (Scrapy + SNCF API)

This project is part of a travel optimizer that scrapes ferry companies (Fromentine ↔ Île d’Yeu) and combines the schedules with the **SNCF API** to build optimized journeys from Paris → Nantes → Fromentine → Île d’Yeu.  
The goal is to maximize **time spent on Île d’Yeu** given user constraints (departure from Paris, return to Paris, optional overnight in Nantes).

---

## ⚙️ Requirements

- Python 3.9+ recommended  
- [Scrapy](https://scrapy.org/)  
- Packages listed in `requirements.txt`  

You should also set up a virtual environment before installing dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

---

## 📂 Project setup

This repository does **not** contain a full Scrapy project, only the modified files you need.
You first need to create a Scrapy project manually, then copy the provided files into the right places.

### 1. Create the Scrapy project

From inside your dev folder:

```bash
scrapy startproject yeu
```

This creates the default structure:

```
yeu/
├── scrapy.cfg
└── yeu/
    ├── __init__.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    └── spiders/
        └── __init__.py
```

### 2. Copy the modified files

Now copy the files from this repo into your newly created Scrapy project:

* `yeu/scrapy.cfg` → overwrite the default one
* `yeu/yeu/items.py` → overwrite
* `yeu/yeu/middlewares.py` → overwrite
* `yeu/yeu/pipelines.py` → overwrite
* `yeu/yeu/settings.py` → overwrite
* `yeu/yeu/spiders/yc_boat_spider.py` → add this spider
* `sncf/sncf_api.py` → helper module for SNCF API calls

At this point your project tree should look like:

```
.
├── requirements.txt
├── scrapy.cfg
├── sncf/
│   └── sncf_api.py
└── yeu/
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    └── spiders/
        └── yc_boat_spider.py
```

---

## 🏃 Usage

### 1. Run the spider

From the project root (where `scrapy.cfg` is):

```bash
scrapy crawl yc_boat_spider -o items.json
```

This will scrape the ferry timetables and export results into `items.json`.

### 2. Work with the SNCF API

You can query the SNCF API using the helper script in `sncf/sncf_api.py`.
Example (run inside a Python shell):

```python
from sncf.sncf_api import get_journeys

data = get_journeys("admin:fr:44109", "admin:fr:85012", "20250908T181500")
print(data["journeys"])
```

---

## 📝 Notes

* The Scrapy pipeline (`pipelines.py`) has regex logic to normalize ferry timetables into a format compatible with SNCF API data.
* All junk files (`.scrapy/`, logs, JSON exports, cache, etc.) are ignored thanks to `.gitignore`.
* Only the files you actually need to reproduce the workflow are tracked here.

---

## 📜 License

This project is for educational/demo purposes. Use responsibly.


