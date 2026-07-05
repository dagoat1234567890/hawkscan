import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_yahoo(query):
    url = f"https://search.yahoo.com/search?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"Yahoo status: {res.status_code}")
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for div in soup.find_all("div", class_="algo"):
                a = div.find("a")
                title = a.get_text(strip=True) if a else ""
                href = a.get("href", "") if a else ""
                
                snippet_elem = div.find("div", class_="compText")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if title and href:
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })
            return results
    except Exception as e:
        print(f"Yahoo error: {e}")
    return []

if __name__ == "__main__":
    q = "100g silver bar site:noon.com"
    print(f"Searching Yahoo for: {q}")
    res = search_yahoo(q)
    print(f"Found {len(res)} results:")
    for r in res:
        print(r)
