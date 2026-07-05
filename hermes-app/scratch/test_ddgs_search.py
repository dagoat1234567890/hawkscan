import traceback
from duckduckgo_search import DDGS

def test():
    with DDGS() as ddgs:
        queries = [
            "100g silver bar noon",
            "iPhone 15 noon",
            "iPhone 15 site:noon.com"
        ]
        for q in queries:
            print(f"Query: {q}")
            try:
                # Use DDGS.text to fetch results
                results = list(ddgs.text(q, max_results=5))
                print(f"Found {len(results)} results:")
                for r in results:
                    print(f"  Title: {r.get('title')}")
                    # print(f"  URL: {r.get('href')}")
                    print(f"  Snippet: {r.get('body')}")
                    print()
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    test()
