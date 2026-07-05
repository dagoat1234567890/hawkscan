import traceback
try:
    from duckduckgo_search import DDGS
    print("DDGS imported successfully.")
    for r in DDGS().text("100g silver bar noon.com", max_results=3):
        print(r)
except Exception as e:
    print("DDGS failed:")
    traceback.print_exc()
