import sys
from pathlib import Path

# Insert the src folder at the front of sys.path for every test session
src_path = Path(__file__).resolve().parents[1] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))