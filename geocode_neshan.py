"""
Optional step: geocode the addresses with the Neshan API (address -> latitude/longitude).

    set NESHAN_API_KEY=service.xxxxx
    python geocode_neshan.py              # resumable; results are cached in work/geocode.csv
    python geocode_neshan.py --limit 500  # test on a small sample

Warning: the addresses are sent to Neshan's service. Check the URL and the response
format against the documentation of your API key's version (the code reads location.x/location.y).
"""
import argparse
import csv
import os
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).parent
CACHE = ROOT / "work" / "geocode.csv"
URL = os.environ.get("NESHAN_GEOCODE_URL", "https://api.neshan.org/v6/geocoding")


def geocode(session, key, address, city):
    r = session.get(URL, params={"address": f"{city} {address}"},
                    headers={"Api-Key": key}, timeout=15)
    if r.status_code == 429:
        time.sleep(5)
        return geocode(session, key, address, city)
    r.raise_for_status()
    js = r.json()
    loc = js.get("location") or {}
    if js.get("status") == "OK" and "x" in loc:
        return float(loc["y"]), float(loc["x"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sleep", type=float, default=0.1, help="pause between requests (seconds)")
    a = ap.parse_args()
    key = os.environ.get("NESHAN_API_KEY")
    if not key:
        raise SystemExit("Set the NESHAN_API_KEY environment variable.")

    df = pd.read_pickle(ROOT / "work" / "clean.pkl")
    df = df[~df.is_duplicate]
    done = set(pd.read_csv(CACHE, dtype=str)["gln"]) if CACHE.exists() else set()
    todo = df[~df.gln.isin(done)]
    if a.limit:
        todo = todo.head(a.limit)
    print(f"done {len(done)}, remaining {len(todo)}")

    new = not CACHE.exists()
    with open(CACHE, "a", newline="", encoding="utf-8") as f, requests.Session() as s:
        w = csv.writer(f)
        if new:
            w.writerow(["gln", "lat", "lon", "status"])
        for n, r in enumerate(todo.itertuples(index=False), 1):
            try:
                res = geocode(s, key, r.address, r.city)
                w.writerow([r.gln, *(res or ("", "")), "ok" if res else "not_found"])
            except requests.RequestException as e:
                w.writerow([r.gln, "", "", f"error:{type(e).__name__}"])
            if n % 100 == 0:
                f.flush(); print(n)
            time.sleep(a.sleep)


if __name__ == "__main__":
    main()
