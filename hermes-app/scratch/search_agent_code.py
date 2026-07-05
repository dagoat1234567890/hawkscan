import os
import re

site_packages_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages"
agent_dir = os.path.join(site_packages_dir, "agent")

print(f"Scanning files in {agent_dir} for browser/fetch keywords...")

keywords = [r"browser", r"playwright", r"fetch", r"scrape", r"selenium", r"web"]
regex = re.compile("|".join(keywords), re.IGNORECASE)

if os.path.exists(agent_dir):
    for root, dirs, files in os.walk(agent_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        matches = regex.findall(content)
                        if matches:
                            # Count unique matches
                            unique_matches = set(m.lower() for m in matches)
                            print(f"File: {os.path.relpath(path, agent_dir)}")
                            print(f"  Keywords found: {unique_matches}")
                except Exception as e:
                    pass
else:
    print("Agent folder does not exist.")
