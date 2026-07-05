import urllib.parse
import sys
from hermes import HawkscanAgent

with open("scratch/test_out.txt", "w", encoding="utf-8") as f:
    try:
        agent = HawkscanAgent()
        f.write("Testing DDG scraper with '100g silver bar site:noon.com'\n")
        listings = agent._search_ddg_html("100g silver bar site:noon.com")
        f.write(f"Listings found: {len(listings)}\n")
        for l in listings:
            f.write(f"{l['title']} - {l['url']}\n")

        f.write("\nTesting DDG scraper with '100g silver bar noon'\n")
        listings = agent._search_ddg_html("100g silver bar noon")
        f.write(f"Listings found: {len(listings)}\n")
        for l in listings:
            f.write(f"{l['title']} - {l['url']}\n")
    except Exception as e:
        f.write(f"Exception occurred: {e}\n")
