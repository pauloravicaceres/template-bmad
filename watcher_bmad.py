"""Legacy public entry point; functions remain import-compatible for consumers/tests."""
import sys
from bmad_runtime import workflow

if __name__ == '__main__':
    raise SystemExit(workflow.main())
else:
    sys.modules[__name__] = workflow
