import os

ddgs_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\plugins\web\ddgs"
print("Files in plugins/web/ddgs:")
for f in os.listdir(ddgs_dir):
    print("  -", f)
    
brave_dir = r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages\plugins\web\brave_free"
print("\nFiles in plugins/web/brave_free:")
for f in os.listdir(brave_dir):
    print("  -", f)
