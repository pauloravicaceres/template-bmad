"""Absolute-path entry point for bootstrap and dry-run/confirmed migration."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bmad_runtime.workspace import main

if __name__ == '__main__':
    raise SystemExit(main())
