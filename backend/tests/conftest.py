import sys
import os

# Ensure backend directory is in sys.path regardless of where pytest is invoked from
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
