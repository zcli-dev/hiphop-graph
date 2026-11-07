import json
import os
import time

import requests

CONTACT = "zcli.dev@gmail.com"
HEADERS = {"User-Agent": f"hiphop-graph/0.1 ( {CONTACT} )"}
BASE = "https://musicbrainz.org/ws/2"
ARTISTS_FILE = "artists.json"
OUT_FILE = "credits.json"
PAGE_SIZE = 100
MAX_PAGES = 3
SKIP_NAMES = {"Various Artists", "[unknown]"}


def get(url, params):
    params = {**params, "fmt": "json"}
    for attempt in range(5):
        time.sleep(1.1)
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"  connection problem, retrying (attempt {attempt + 1})...")
            time.sleep(5 * (attempt + 1))
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 503):
            time.sleep(5 * (attempt + 1))
            continue
        resp.raise_for_status()
    raise RuntimeError("Gave up on " + url)


def collaborators_in(page, seed_id):
    found = {}
    for recording in page.get("recordings", []):
        seen = set()
        for credit in recording.get("artist-credit", []):
            artist = credit.get("artist")
            if not artist or artist["id"] == seed_id or artist["id"] in seen:
                continue
            if artist["name"] in SKIP_NAMES:
                continue
            seen.add(artist["id"])
            entry = found.setdefault(artist["id"], {"name": artist["name"], "count": 0})
            entry["count"] += 1
    return found


def fetch_collaborators(seed_id):
    combined = {}
    for page_number in range(MAX_PAGES):
        page = get(
            f"{BASE}/recording",
            {"artist": seed_id, "inc": "artist-credits", "limit": PAGE_SIZE, "offset": page_number * PAGE_SIZE},
        )
        for artist_id, info in collaborators_in(page, seed_id).items():
            entry = combined.setdefault(artist_id, {"name": info["name"], "count": 0})
            entry["count"] += info["count"]
        if (page_number + 1) * PAGE_SIZE >= page.get("recording-count", 0):
            break
    return combined


def load_existing():
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(credits):
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(credits, f, indent=2)


def main():
    with open(ARTISTS_FILE, encoding="utf-8") as f:
        seeds = json.load(f)

    credits = load_existing()
    todo = [a for a in seeds if a["id"] not in credits]
    print(f"Already have {len(credits)} artists, {len(todo)} to go, roughly {len(todo) * MAX_PAGES * 1.2 / 60:.0f} minutes at most")

    try:
        for i, seed in enumerate(todo, 1):
            collaborators = fetch_collaborators(seed["id"])
            credits[seed["id"]] = {"name": seed["name"], "collaborators": collaborators}
            print(f"[{i}/{len(todo)}] {seed['name']}: {len(collaborators)} collaborators")
            if i % 10 == 0:
                save(credits)
    finally:
        save(credits)
        print(f"Saved {len(credits)} artists to {OUT_FILE}")


main()