import requests
import traceback

def test():
    # Try different user agents and headers
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ]
    
    for ua in uas:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1"
        }
        
        url = "https://www.noon.com/uae-en/search/?q=100g+silver+bar"
        print(f"Testing UA: {ua}")
        try:
            res = requests.get(url, headers=headers, timeout=5)
            print(f"Status Code: {res.status_code}")
            print(f"Content Length: {len(res.text)}")
            if res.status_code == 200:
                print("Success! Head of content:")
                print(res.text[:300])
                break
        except Exception as e:
            print(f"Failed: {e}")
        print()

if __name__ == "__main__":
    test()
