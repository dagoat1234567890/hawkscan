import os

tools_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\tools"
print("Contents of tools directory:")
for root, dirs, files in os.walk(tools_dir):
    rel_path = os.path.relpath(root, tools_dir)
    if rel_path == ".":
        print("Root level dirs:", dirs)
        print("Root level files:", [f for f in files if f.endswith(".py")])
    elif rel_path.count(os.sep) == 0:
        print(f"  Subdir: {rel_path} -> files: {[f for f in os.listdir(root) if f.endswith('.py')]}")
