import requests

url = "https://musicbrainz.org/ws/2/artist"
params = {"query": "Kendrick Lamar", "limit": 1, "fmt": "json"}
headers = {"User-Agent": "hiphop-graph/0.1 ( zcli.dev@gmail.com )"}

response = requests.get(url, params=params, headers=headers)
data = response.json()
print(data["artists"][0]["name"])