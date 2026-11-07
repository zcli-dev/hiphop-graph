# Hip-Hop Connections

**Live site: https://zcli-dev.github.io/hiphop-graph/**

An explorable graph of hip-hop artists, built from open music data. Look up an artist to see who they've worked with and who's similar, or pick two artists to see the shortest chain of collaborations between them.

## What it does

- **Find similar artists:** shows an artist's closest collaborators, plus other artists who work with many of the same people.
- **How are two artists connected?** finds the shortest chain of connections between any two artists and explains each step (for example, "credited on 12 songs together").

## How it works

1. `ingest.py` searches MusicBrainz for artists tagged hip hop, keeps those with at least 3 hip-hop tag votes, and saves their relationships with other artists.
2. `credits.py` reads up to 300 recordings per artist and counts which other artists are credited alongside them.
3. `export.py` merges both sources into one graph, keeps song-credit links with at least 2 shared songs, keeps the largest connected cluster, and exports it as `graph.json` (5,590 artists and 9,988 connections).
4. The website (`index.html`, `app.js`, `style.css`) loads `graph.json` in the browser. Shortest paths use a breadth-first search. Similar artists are ranked by shared collaborators, with very well-connected collaborators weighted less (Adamic-Adar). Cytoscape.js draws the small neighborhood that is relevant to each search.

## Data and attribution

Data comes from [MusicBrainz](https://musicbrainz.org), whose core data is CC0. Only facts are stored: names, IDs, relationships, and song counts. No lyrics or audio are stored or hosted. Requests follow MusicBrainz's rate limit and User-Agent rules.

## Limitations

- The main artist list comes from the top 500 results of a tag search, so it is not complete or hand-curated.
- Tags are added by users, so a few non-hip-hop artists can appear.
- Song credits are sampled (up to 300 recordings per artist), and MusicBrainz does not order them by popularity.
- MusicBrainz is edited by volunteers, so credits for features and producers are incomplete.
- "Similar" means "shares collaborators," not "sounds alike."

## Run it yourself

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ingest.py
python credits.py
python export.py
python -m http.server 8000
```

Set `CONTACT` at the top of `ingest.py` and `credits.py` to your own email, because MusicBrainz asks API users to identify themselves. Then open http://localhost:8000.

## Built with

Python (requests, networkx), JavaScript, Cytoscape.js, GitHub Pages.