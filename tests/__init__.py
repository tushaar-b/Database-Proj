"""Tests root package."""
import sys
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
