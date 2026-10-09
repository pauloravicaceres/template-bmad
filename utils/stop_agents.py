"""Close verified project-owned idle sessions with explicit authorization."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from bmad_runtime.maintenance import stop_main

if __name__ == '__main__':
    raise SystemExit(stop_main(ROOT))
