import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app\.venv\Lib\site-packages")

import os
# Ensure we run in local mode for the browser tool
os.environ["BROWSER_CLOUD_PROVIDER"] = "local"

from tools.browser_tool import browser_navigate, browser_snapshot, cleanup_browser

task_id = "test_noon_browser"

print("Navigating to Noon search page using local agent-browser...")
try:
    # Navigate
    res = browser_navigate(
        "https://www.noon.com/uae-en/search/?q=100g+silver+bar", 
        task_id=task_id
    )
    print("Navigation Result:", res)
    
    # Get Snapshot
    print("\nTaking snapshot of page...")
    snapshot = browser_snapshot(task_id=task_id)
    print("Snapshot (first 1000 characters):")
    print(snapshot[:1000])
    
finally:
    print("\nCleaning up browser...")
    cleanup_browser(task_id)
