import requests

candidates = ["airbnb", "figma", "discord", "robinhood", "coinbase",
              "databricks", "datadog", "reddit"]

for token in candidates:
    r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{token}", timeout=10)
    if r.status_code == 200:
        print(f"OK   {token:15} {r.json().get('name')}")
    else:
        print(f"MISS {token:15} HTTP {r.status_code}")