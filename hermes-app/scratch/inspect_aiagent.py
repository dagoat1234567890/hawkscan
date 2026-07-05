import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages")
from run_agent import AIAgent

agent = AIAgent()
print("AIAgent methods/properties:")
for name in dir(agent):
    if not name.startswith("_"):
        print(f"  {name}")

# Let's inspect the tools loaded by AIAgent
try:
    print("\nAttempting to get tools...")
    # Does AIAgent have a tools property? Let's check keys/attributes of agent
    for k, v in agent.__dict__.items():
        if "tool" in k or "function" in k:
            print(f"  {k}: {type(v)}")
except Exception as e:
    print("Error getting tools:", e)
