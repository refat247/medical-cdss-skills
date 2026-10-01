"""Backward-compatible CLI wrapper redirecting to unified_orchestrator.py."""
import sys
from pathlib import Path

# Ensure local script directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from unified_orchestrator import main

if __name__ == "__main__":
    main()
