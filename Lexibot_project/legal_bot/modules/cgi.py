# cgi.py (shim for Python 3.13)
# Only to bypass imports that break due to removed cgi module
import warnings
warnings.warn("cgi module not available in Python 3.13, using shim.")

# Define minimal classes/functions used by langchain-core if needed
class FieldStorage:
    pass

# You can add more stubs if errors appear
