"""
PDF Anonymizer – Entry point.

Starts the PyQt6 GUI application for AI-powered PDF anonymisation.
"""

import sys
import os

# Ensure the src directory is on the path (needed for PyInstaller bundles)
if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from gui import run_app

if __name__ == "__main__":
    run_app()
