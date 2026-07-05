import sys
import os

sys.path.append(os.getcwd())

# Import the Flask app object and rename it to 'application' for Hostinger
from app import app as application
