import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app")
from hermes import HawkscanAgent

agent = HawkscanAgent()
platform_domain = "noon.com"
query1 = f"100g silver bar site:{platform_domain}"
listings = agent._search_ddg_html(query1)
print(f"DuckDuckGo HTML listings for '{query1}':")
for i, item in enumerate(listings, 1):
    print(f"#{i}: {item['title']}")
    print(f"   URL: {item['url']}")
    print(f"   Snippet: {item['snippet']}")
    print()

query2 = "100g silver bar Noon price UAE"
broad_listings = agent._search_ddg_html(query2)
print(f"\nDuckDuckGo HTML broad listings for '{query2}':")
for i, item in enumerate(broad_listings, 1):
    print(f"#{i}: {item['title']}")
    print(f"   URL: {item['url']}")
    print(f"   Snippet: {item['snippet']}")
    print()
