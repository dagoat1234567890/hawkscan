import urllib.parse
from hermes import HawkscanAgent

agent = HawkscanAgent()
print("Testing DDG scraper with '100g silver bar site:noon.com'")
listings = agent._search_ddg_html("100g silver bar site:noon.com")
print(f"Listings found: {len(listings)}")
for l in listings:
    print(l['title'], l['url'])

print("\nTesting DDG scraper with '100g silver bar noon'")
listings = agent._search_ddg_html("100g silver bar noon")
print(f"Listings found: {len(listings)}")
for l in listings:
    print(l['title'], l['url'])
