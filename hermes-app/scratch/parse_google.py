from bs4 import BeautifulSoup

def parse_local():
    with open(r"C:\Users\Shagy\Documents\hermes-app\scratch\google.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    print("Page Title:", soup.title.get_text() if soup.title else "No Title")
    
    # Check if there is a CAPTCHA or blocking message
    if "captcha" in html.lower() or "unusual traffic" in html.lower():
        print("ALERT: Google blocked us (CAPTCHA/unusual traffic detected).")
        return
        
    print("\nLinks and Anchors found in page:")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href and ("noon" in href or "noon" in text.lower()):
            links.append((text, href))
            
    print(f"Found {len(links)} links related to noon:")
    for text, href in links[:15]:
        print(f"  {text} -> {href}")

if __name__ == "__main__":
    parse_local()
