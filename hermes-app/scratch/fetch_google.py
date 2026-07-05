import requests

def fetch_and_save():
    url = "https://www.google.com/search?q=100g+silver+bar+site:noon.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        with open(r"C:\Users\Shagy\Documents\hermes-app\scratch\google.html", "w", encoding="utf-8") as f:
            f.write(res.text)
        print("Saved Google response HTML.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_save()
