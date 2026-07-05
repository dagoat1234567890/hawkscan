import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app")
from hermes import HawkscanAgent

agent = HawkscanAgent()
listings = agent._fetch_amazon_search_direct("100g silver bar")
print(f"Direct Amazon search returned {len(listings)} listings:")
for i, item in enumerate(listings, 1):
    print(f"#{i}: {item['title']}")
    print(f"   URL: {item['url']}")
    print(f"   Snippet (first 200 chars): {item['snippet'][:200]}")
    print()
