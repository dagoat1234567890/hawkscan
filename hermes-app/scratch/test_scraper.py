import os
import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app")
from dotenv import load_dotenv
load_dotenv(r"C:\Users\Shagy\Documents\hermes-app\.env")

from hermes import HawkscanAgent

def test():
    agent = HawkscanAgent()
    print("Testing Noon price analysis...")
    res = agent.analyze_prices("100g silver bar", "Kannan Jewelers", "Noon")
    print("Result:", res)

if __name__ == "__main__":
    test()
