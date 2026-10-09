"""Initialize a project without copying the shared BMAD engine."""
import sys
from bmad_runtime.workspace import main

if __name__ == '__main__':
    raise SystemExit(main(['init', *sys.argv[1:]]))
