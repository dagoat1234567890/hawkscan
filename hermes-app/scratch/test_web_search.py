import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages")

import os
# Configure tools config to use ddgs search backend
os.environ["HERMES_WEB_SEARCH_BACKEND"] = "ddgs"

from tools.web_tools import _ensure_web_plugins_loaded, web_search_tool
import agent.web_search_registry as registry

_ensure_web_plugins_loaded()

print("Registered search providers:")
for p in registry.list_providers():
    print(f"  - {p.name} (available: {p.is_available()})")

print("\nRunning web search using web_search_tool...")
try:
    res = web_search_tool("100g silver bar noon", limit=5)
    print("Search Result:")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
