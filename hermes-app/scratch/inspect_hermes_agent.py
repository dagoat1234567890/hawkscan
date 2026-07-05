import sys
import traceback

print("Python version:", sys.version)

try:
    # Try importing NousResearch hermes_agent or similar
    import hermes_agent
    print("Successfully imported hermes_agent!")
    print("hermes_agent modules/dir:", dir(hermes_agent))
except ImportError:
    print("Could not import hermes_agent:")
    traceback.print_exc()

try:
    # Let's inspect packages in site-packages containing hermes
    import site
    import os
    for p in site.getsitepackages():
        print("Searching site-package:", p)
        if os.path.exists(p):
            for folder in os.listdir(p):
                if "hermes" in folder.lower() or "agent" in folder.lower():
                    print("  Found folder:", folder)
except Exception as e:
    print("Error scanning site packages:", e)
