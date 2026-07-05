import sys

try:
    import playwright
    print("playwright is installed!")
except ImportError:
    print("playwright is NOT installed.")

try:
    import selenium
    print("selenium is installed!")
except ImportError:
    print("selenium is NOT installed.")
