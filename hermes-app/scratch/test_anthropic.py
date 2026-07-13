import os
import sys
from hermes import HawkscanAgent

def test():
    agent = HawkscanAgent()
    try:
        messages = [{"role": "user", "content": "Hello!"}]
        text, tokens = agent._call_anthropic(messages)
        print(f"Success! Tokens: {tokens}")
        print(text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test()
