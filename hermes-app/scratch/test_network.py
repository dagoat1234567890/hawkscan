import requests

domains = [
    "https://www.google.com",
    "https://html.duckduckgo.com/html/",
    "https://lite.duckduckgo.com/lite/",
    "https://www.bing.com",
    "https://www.noon.com",
    "https://www.amazon.ae"
]

for d in domains:
    try:
        res = requests.get(d, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        print(f"{d} - Success: status code {res.status_code}")
    except Exception as e:
        print(f"{d} - Failed: {e}")
