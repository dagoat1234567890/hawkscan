import requests

def test():
    # Try requesting Noon with NO Accept-Encoding or just gzip, deflate
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    url = "https://www.noon.com/uae-en/search/?q=100g+silver+bar"
    print("Testing Noon direct request without br encoding...")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        print(f"Content Length: {len(res.text)}")
        if res.status_code == 200:
            print("Success! Title tag:")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            print(soup.title)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test()
