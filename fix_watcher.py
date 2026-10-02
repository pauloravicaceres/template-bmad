import sys
from pathlib import Path

content = Path("watcher_bmad.py").read_text(encoding="utf-8")

# Fix the broken quotes and print statement
content = content.replace('" " "\n    Hito 3 del SDD Auto-Runner: Fase D', '"""\n    Hito 3 del SDD Auto-Runner: Fase D')
content = content.replace('Soul Mounting.\n    " " "\n    print(f"\n', 'Soul Mounting.\n    """\n    print(f"\\n')
content = content.replace('?? [SDD', '⚙️ [SDD')

Path("watcher_bmad.py").write_text(content, encoding="utf-8")