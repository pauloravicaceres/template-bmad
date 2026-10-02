import os

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

broken = 'if "@dev-back:" in linea_lower or "@dev-front:" in linea_lower:'
fixed = 'if ("@dev-back:" in linea_lower or "@dev-front:" in linea_lower) and "arquitectura" in linea_lower:'

content = content.replace(broken, fixed)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)