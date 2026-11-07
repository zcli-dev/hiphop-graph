import json
import os
import time

import requests

CONTACT = "zcli.dev@gmail.com"
HEADERS = {"User-Agent": f"hiphop-graph/0.1 ( {CONTACT} )"}
BASE = "https://musicbrainz.org/ws/2"
OUT_FILE = "artists.json"
LIMIT = 300
MIN_TAG_COUNT = 3
HIPHOP_TAGS = {"hip hop", "hip-hop", "rap"}
SKIP_NAMES = {"Various Artists"}


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


def hiphop_votes(artist):
    return sum(t.get("count", 0) for t in artist.get("tags", []) if t["name"].lower() in HIPHOP_TAGS)


def find_artists(limit):
    candidates = []
    offset = 0
    while len(candidates) < limit:
        try:
            page = get(f"{BASE}/artist", {"query": 'tag:"hip hop"', "limit": 100, "offset": offset})
        except requests.exceptions.HTTPError as error:
            print(f"Stopped paging at offset {offset}: {error}")
            break
        results = page["artists"]
        if not results:
            break
        for artist in results:
            if artist["name"] not in SKIP_NAMES and hiphop_votes(artist) >= MIN_TAG_COUNT:
                candidates.append(artist)
        offset += len(results)
        print(f"Searched {offset} results, kept {len(candidates)}")
    candidates.sort(key=hiphop_votes, reverse=True)
    return candidates[:limit]


def clean_relations(artist_data):
    links = []
    for rel in artist_data.get("relations", []):
        other = rel.get("artist")
        if rel.get("target-type") == "artist" and other:
            links.append({"type": rel["type"], "other_id": other["id"], "other_name": other["name"]})
    return links


def load_existing():
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save(results):
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def main():
    results = load_existing()
    done = {a["id"] for a in results}
    print(f"Already have {len(results)} artists")

    found = find_artists(LIMIT)
    todo = [a for a in found if a["id"] not in done]
    print(f"{len(todo)} new artists to fetch, roughly {len(todo) * 1.2 / 60:.0f} minutes")

    try:
        for i, artist in enumerate(todo, 1):
            detail = get(f"{BASE}/artist/{artist['id']}", {"inc": "artist-rels"})
            results.append(
                {
                    "id": detail["id"],
                    "name": detail["name"],
                    "country": detail.get("country"),
                    "relations": clean_relations(detail),
                }
            )
            print(f"[{i}/{len(todo)}] {detail['name']}: {len(results[-1]['relations'])} links")
            if i % 10 == 0:
                save(results)
    finally:
        save(results)
        print(f"Saved {len(results)} artists to {OUT_FILE}")


main()