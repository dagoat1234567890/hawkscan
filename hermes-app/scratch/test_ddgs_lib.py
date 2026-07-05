import traceback
from duckduckgo_search import DDGS

try:
    print("Trying duckduckgo_search text search...")
    with DDGS() as ddgs:
        results = list(ddgs.text("100g silver bar site:noon.com", max_results=5))
        print("Success! Results:")
        for r in results:
            print(r)
except Exception as e:
    print("DDGS failed:")
    traceback.print_exc()
