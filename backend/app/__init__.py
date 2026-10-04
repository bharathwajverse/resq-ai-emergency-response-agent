"""
ResQ-AI Backend Application Package.
Ensures backend root is in sys.path for robust absolute imports.
"""

import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

__version__ = "1.0.0"
