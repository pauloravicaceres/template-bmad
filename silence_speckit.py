import os
import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

broken = """subprocess.run('agy --dangerously-skip-permissions --print "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)"""
fixed = """subprocess.run('agy --dangerously-skip-permissions "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"""

content = content.replace(broken, fixed)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)