import os
from hermes import HawkscanAgent
from unittest.mock import MagicMock

def test():
    agent = HawkscanAgent()
    # Mock Anthropic call
    agent._call_anthropic = MagicMock(return_value=('{"my_price": 100, "competitors": []}', 250))
    # Mock requests to skip network
    agent._fetch_amazon_search_direct = MagicMock(return_value=[])
    agent._fetch_noon_search_direct = MagicMock(return_value=[])
    
    results = agent.analyze_prices("iPhone 15", "Apple", "Amazon")
    print(results)

if __name__ == '__main__':
    test()
