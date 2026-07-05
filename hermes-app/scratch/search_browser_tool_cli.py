with open(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\tools\browser_tool.py", "r", encoding="utf-8") as f:
    code = f.read()

import re
matches = [line for line in code.splitlines() if "subprocess" in line.lower() or "agent-browser" in line.lower() or "cmd" in line.lower()]
print(f"Found {len(matches)} matching lines in browser_tool.py:")
for m in matches[:30]:
    ascii_line = m.encode("ascii", errors="replace").decode("ascii")
    print(ascii_line)
