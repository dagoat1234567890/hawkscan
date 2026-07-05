from duckduckgo_search import DDGS

def test():
    with DDGS() as ddgs:
        queries = [
            "silver bar noon",
            "noon \"silver bar\"",
            "noon.com silver bar",
            "noon silver bar uae",
            "emirates gold silver bar noon"
        ]
        for q in queries:
            print(f"=== Query: {q} ===")
            try:
                results = list(ddgs.text(q, max_results=5))
                print(f"Found {len(results)} results:")
                for r in results:
                    print(f"  Title: {r.get('title')}")
                    print(f"  URL: {r.get('href')}")
                    print(f"  Snippet: {r.get('body')}")
                    print()
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    test()
