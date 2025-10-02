# 🚤 Paris → Île d’Yeu Trip Planner (Scrapy + SNCF API)

This project is part of a travel optimizer that scrapes ferry companies (Fromentine ↔ Île d’Yeu) and combines the schedules with the **SNCF API** to build optimized journeys from Paris → Nantes → Fromentine → Île d’Yeu.
The goal is to maximize **time spent on Île d’Yeu** given user constraints (departure from Paris, return to Paris, optional overnight in Nantes).

---

## ⚡ Quickstart (Docker – Recommended)

BEFORE Anything you will need to get your own sncf API token (it is free and available here https://www.digital.sncf.com/startup/api)

You don’t need to install Python, Scrapy, or dependencies manually.
The simplest way to run this project is using the prebuilt Docker image:

```bash
docker run --rm your-dockerhub-username/yeu-voyage-planner <your_api_key> \
  --start 2025-10-16T17:15:00 \
  --end 2025-10-20T13:00:00
```

Example with a **fake key**:

```bash
docker run --rm your-dockerhub-username/yeu-voyage-planner
xxxx-xxxx-xxxx \
  --start 2025-10-16T17:15:00 \
  --end 2025-10-20T13:00:00
```

✅ This will generate two JSON files:

* `final_voyage_plan_outbound.json` → Paris → Nantes → Fromentine → Île d’Yeu
* `final_voyage_plan_return.json` → Île d’Yeu → Fromentine → Nantes → Paris

👉 [View DockerHub image here](https://hub.docker.com/r/your-dockerhub-username/yeu-voyage-planner)

---

## ⚙️ Advanced setup (manual / dev)

If you want to hack the code or run things outside Docker, you’ll need to set up the Python + Scrapy environment manually.

### Requirements

* Python 3.9+ recommended
* [Scrapy](https://scrapy.org/)
* Packages listed in `requirements.txt`

Set up a virtual environment before installing dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📂 Project setup

⚠️ This repo does **not** include a full Scrapy project (to keep it lightweight).
You’ll need to create a Scrapy project yourself and copy in the provided files.

### 1. Create the Scrapy project

```bash
scrapy startproject yeu
```

Project structure:

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

### 2. Copy the provided files

Overwrite or add the following files from this repo:

* `yeu/scrapy.cfg`
* `yeu/yeu/items.py`
* `yeu/yeu/middlewares.py`
* `yeu/yeu/pipelines.py`
* `yeu/yeu/settings.py`
* `yeu/yeu/spiders/yc_boat_spider.py`
* `sncf/sncf_api.py`

Final tree:

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

## 🏃 Usage (manual mode)

### 1. Run the spider

### 2. Run the spider
Inside yeu folder (no need to go further)
```
scrapy crawl yc_boat -a date=16/10/2025 -O boats.json
```
Example for scrapping boats on the month of October, results will be available in boats.json

This scrapes ferry timetables into `items.json`.

### 3. Use the SNCF API

Inside sncf folder:

```
python sncf_api.py <YOU SNCF API KEY> nantes fromentine_la_barre-de-monts 20251017 180000 arrival car_outbound.json
```
Example for looking for a voyage from nantes to fromentine with the arrival as close as possible to 2025 10 17 at 18H00, results will be available in car_outbound.json
---

## 📝 Notes

* The Scrapy pipeline normalizes ferry data to match SNCF API format.
* `.gitignore` filters out junk files (cache, logs, exports).
* Only **essential files** are tracked here.
* The **Docker image is the easiest way** to get a working environment.

---

## 📜 License

For educational/demo purposes only. Use responsibly.

---



