# storage.py
import os
import csv
import json
import pandas as pd

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "results.csv")

def init_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "num_reviews", "summary_json", "details_json"])

def append_record(record: dict):
    """
    record = {
      "timestamp": "...",
      "num_reviews": int,
      "summary": [...],
      "details": [...]
    }
    """
    init_storage()
    with open(DB_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([record.get("timestamp"), record.get("num_reviews"),
                         json.dumps(record.get("summary"), ensure_ascii=False),
                         json.dumps(record.get("details"), ensure_ascii=False)])

def load_records():
    if not os.path.exists(DB_PATH):
        init_storage()
    try:
        df = pd.read_csv(DB_PATH)
        return df
    except Exception:
        # fallback: read raw
        return pd.read_csv(DB_PATH, dtype=str, keep_default_na=False)
