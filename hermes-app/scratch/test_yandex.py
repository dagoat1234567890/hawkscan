import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_yandex():
    query = "100g silver bar site:noon.com"
    url = f"https://yandex.com/search/?text={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"Yandex status: {res.status_code}")
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            print("Title:", soup.title.get_text() if soup.title else "No Title")
            # Check for captcha
            if "captcha" in res.text.lower():
                print("Captcha detected on Yandex.")
                return
            
            # Print first 5 links
            for i, a in enumerate(soup.find_all("a"), 1):
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if href.startswith("http") and "noon" in href:
                    print(f"  #{i}: {text} -> {href}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_yandex()
