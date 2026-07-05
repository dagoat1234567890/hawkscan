import os
import sys

site_packages_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages"
print("Scanning site-packages for plugins...")
for f in os.listdir(site_packages_dir):
    path = os.path.join(site_packages_dir, f)
    if os.path.isdir(path) and "plugin" in f.lower():
        print("  Found plugin directory:", f)
        
try:
    import plugins
    print("Successfully imported plugins package!")
    print("plugins path:", plugins.__path__)
except ImportError:
    print("Could not import plugins.")
