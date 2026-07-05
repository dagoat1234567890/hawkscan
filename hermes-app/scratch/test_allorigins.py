import requests
import json
import urllib.parse
from bs4 import BeautifulSoup

def test_allorigins():
    target_url = "https://html.duckduckgo.com/html/?q=100g+silver+bar+noon"
    proxy_url = f"https://api.allorigins.win/get?url={urllib.parse.quote_plus(target_url)}"
    
    print(f"Requesting proxy: {proxy_url}")
    try:
        res = requests.get(proxy_url, timeout=10)
        print(f"Proxy status code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            contents = data.get("contents", "")
            print(f"Contents length: {len(contents)}")
            soup = BeautifulSoup(contents, "html.parser")
            print("Page Title:", soup.title.get_text() if soup.title else "No Title")
            
            # Print first 3 links
            results = []
            for a in soup.find_all("a", class_="result__snippet"):
                title_elem = a.find_previous("a", class_="result__url")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                snippet = a.get_text(strip=True)
                results.append((title, snippet))
                
            print(f"Found {len(results)} results:")
            for t, s in results[:3]:
                print(f"  Title: {t}")
                print(f"  Snippet: {s}")
                print()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_allorigins()
