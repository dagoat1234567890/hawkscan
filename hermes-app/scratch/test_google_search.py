import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_google_html(query):
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"Google status: {res.status_code}")
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            print("Title:", soup.title)
            print("Snippet:", res.text[:500])
            results = []
            
            # Google search result blocks are usually in div.g
            for g in soup.find_all("div", class_="g"):
                a = g.find("a")
                if not a:
                    continue
                href = a.get("href", "")
                title_elem = g.find("h3")
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                snippet_elem = g.find("div", class_="VwiC3b") or g.find("div", class_="yDAB2d")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if href and title:
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })
            return results
    except Exception as e:
        print(f"Google error: {e}")
    return []

if __name__ == "__main__":
    q = "100g silver bar site:noon.com"
    print(f"Searching Google for: {q}")
    res = search_google_html(q)
    print(f"Found {len(res)} results:")
    for r in res:
        print(r)
