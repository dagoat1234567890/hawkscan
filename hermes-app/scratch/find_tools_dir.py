import os

site_packages_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages"
print("Scanning site-packages for directories containing 'tools':")
for f in os.listdir(site_packages_dir):
    path = os.path.join(site_packages_dir, f)
    if os.path.isdir(path) and "tool" in f.lower():
        print("  Found directory:", f)
