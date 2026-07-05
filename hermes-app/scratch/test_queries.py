from duckduckgo_search import DDGS

with DDGS() as ddgs:
    queries = [
        "100g silver bar Noon.com",
        "100g silver bar Noon price",
        "Emirates Gold 100g silver bar Noon",
        "100g silver bar Noon UAE AED"
    ]
    for q in queries:
        print(f"=== Query: {q} ===")
        try:
            results = list(ddgs.text(q, max_results=8))
            for r in results:
                print(f"Title: {r['title']}")
                print(f"URL: {r['href']}")
                print(f"Snippet: {r['body']}")
                print("-" * 20)
        except Exception as e:
            print(f"Failed: {e}")
        print("\n")
