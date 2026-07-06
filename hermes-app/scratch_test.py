from hermes import HawkscanAgent
from dotenv import load_dotenv
import os

load_dotenv()
agent = HawkscanAgent(api_key=os.environ.get("ANTHROPIC_API_KEY"))

print("Testing iPhone 15 Pro...")
results = agent._fetch_noon_search_direct("Apple iPhone 15 Pro 256GB")
print(f"Noon search found {len(results)} raw results. First result: {results[0]['title'] if results else 'None'}")

print("\nAnalyzing prices...")
json_response = agent.analyze_prices("Apple iPhone 15 Pro 256GB", "Noon", "Apple", "https://noon.com/some-iphone-url", results, "Noon, Apple")
print("\nAI Response:")
print(json_response)
