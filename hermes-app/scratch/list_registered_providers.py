import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages")

try:
    import agent.web_search_registry as registry
    print("Registered web search providers:")
    providers = registry.list_providers()
    print(f"Total: {len(providers)}")
    for p in providers:
        print(f"  - {p.name} (display: {p.display_name}, available: {p.is_available()})")
except Exception as e:
    import traceback
    traceback.print_exc()
