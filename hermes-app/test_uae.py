import os
from dotenv import load_dotenv
load_dotenv()

from hermes import HermesAgent

def test():
    agent = HermesAgent()
    print("Testing Amazon.ae...")
    res1 = agent.analyze_prices("iPhone 15", "Acme Electronics", "Amazon.ae")
    print("Amazon.ae Result:", res1)
    
    print("\nTesting Noon...")
    res2 = agent.analyze_prices("iPhone 15", "Acme Electronics", "Noon")
    print("Noon Result:", res2)

if __name__ == "__main__":
    test()
