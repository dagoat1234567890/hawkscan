import os

plugins_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\plugins"
print("Contents of plugins directory:")
for root, dirs, files in os.walk(plugins_dir):
    rel_path = os.path.relpath(root, plugins_dir)
    if rel_path == ".":
        print("Root level dirs:", dirs)
    elif rel_path.count(os.sep) == 0:
        print(f"  Category: {rel_path} -> subdirs: {dirs}")
