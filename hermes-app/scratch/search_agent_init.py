import sys

with open(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\agent\agent_init.py", "r", encoding="utf-8") as f:
    code = f.read()

import re
matches = [line for line in code.splitlines() if "plugin" in line.lower() or "load" in line.lower()]
print(f"Found {len(matches)} matching lines in agent_init.py:")
for m in matches[:30]:
    # Strip non-ascii characters
    ascii_line = m.encode("ascii", errors="replace").decode("ascii")
    print(ascii_line)
